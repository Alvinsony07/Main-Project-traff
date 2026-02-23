import cv2
import threading
import time
from models.vehicle_detector import VehicleDetector
from models.ambulance_detector import AmbulanceDetector
from models.traffic_logic import TrafficLogic
from database.models import db, LaneStats, VehicleLog, AmbulanceEvent
from flask import current_app

class VideoProcessor:
    def __init__(self, config, app):
        self.config = config
        self.app = app # Flask app context for DB operations
        
        self.vehicle_detector = VehicleDetector(config.MODEL_VEHICLE_PATH)
        self.ambulance_detector = AmbulanceDetector(config.MODEL_AMBULANCE_PATH)
        self.traffic_logic = TrafficLogic(config)
        
        # Store latest processing results
        self.frame_data = {} # {0: frame, 1: frame, ...}
        # Updated to include 'details' for broken down counts
        self.lane_data = {i: {'count': 0, 'density': 'Low', 'details': {}} for i in range(4)}
        self.ambulance_active = [False] * 4 # Track ambulance state per lane
        
        self.caps = [None] * 4
        self.sources = [None] * 4 # Paths to video files
        
        self.running = False
        self.thread = None

    def start_streams(self, video_paths):
        """
        Initialize video captures
        video_paths: list of 4 file paths or stream URLs
        """
        # Stop existing thread/streams if running to prevent conflict
        if self.running or (self.thread and self.thread.is_alive()):
            self.stop()
            # Give it a moment to release resources
            time.sleep(0.5)

        self.sources = video_paths
        for i, src in enumerate(video_paths):
            if src:
                self.caps[i] = cv2.VideoCapture(src)
        
        self.running = True
        self.thread = threading.Thread(target=self._process_loop)
        self.thread.daemon = True
        self.thread.start()

    def _process_loop(self):
        """
        Main processing loop.
        Reads frames from all active sources, runs detection, updates stats.
        """
        # Optimization: Run detection every N frames
        # Staggered: 4 lanes, Interval 4 means 1 lane processed per frame
        DETECT_INTERVAL = 4 
        frame_count = 0
        
        cached_boxes = {i: {'vehicles': [], 'ambulance': []} for i in range(4)}
        
        # Get signal controller once (Global object, doesn't need context every frame)
        current_signal_logic = self.app.config.get('SIGNAL_CONTROLLER')
        
        while self.running:
            # Loop delay to stabilize FPS around 30
            start_time = time.time()
            
            for i in range(4):
                try:
                    if self.caps[i] and self.caps[i].isOpened():
                        ret, raw_frame = self.caps[i].read()
                        if not ret:
                            self.caps[i].set(cv2.CAP_PROP_POS_FRAMES, 0)
                            continue
                            
                        # Downscale
                        frame = cv2.resize(raw_frame, (480, 270))
                        
                        # -- STAGGERED DETECTION LOGIC --
                        # Only process 1 lane per frame to distribute load
                        if (frame_count + i) % DETECT_INTERVAL == 0:
                            
                            # 1. Detect All Vehicles (No drawing yet)
                            # We get vehicle_boxes: [{'coords':(x1,y1,x2,y2), ...}]
                            _, counts, total, veh_data_list = self.vehicle_detector.detect(frame, draw=False)

                            # Extract just boxes for ambulance check
                            raw_boxes = [v['coords'] for v in veh_data_list]

                            # 2. Check if any vehicle is an ambulance
                            # This reuses the boxes, avoiding a 2nd YOLO call
                            has_ambu, _, ambu_boxes = self.ambulance_detector.check_boxes(frame, raw_boxes)
                            
                            self.ambulance_active[i] = has_ambu
                            
                            # Cache Ambulance Boxes
                            cached_boxes[i]['ambulance'] = ambu_boxes
                            
                            # Cache Vehicle Boxes (excluding ambulances for drawing if needed, 
                            # or just separate them. Vehicles are already classified by YOLO)
                            cached_boxes[i]['vehicles'] = veh_data_list

                            # Start Counting Logic
                            # If ambulance is found, technically it was counted as a 'truck' or 'car' usually.
                            # We can leave the count as is, or adjust. 
                            # User cares about 'Traffic Logic', so Ambulance presence is more important than -1 car count.

                            # Update Stats
                            self.lane_data[i]['count'] = total
                            self.lane_data[i]['details'] = counts 
                            density_label = self.traffic_logic.get_density_label(total)
                            self.lane_data[i]['density'] = density_label
                            
                            # DB logging: periodically
                            current_time = time.time()
                            if getattr(self, 'last_db_log', 0) + 5 < current_time:
                                try:
                                    # Simple check to avoid spamming too many DB commits if we are running 4 lanes
                                    # Just allow Lane 0 to trigger the commit for everyone, or check per lane
                                    # But we only updated Lane 'i' stats here. 
                                    # Let's just log when Lane 0 processes, or use a separate timer.
                                    # For simplicity, log THIS lane's stats now.
                                    with self.app.app_context():
                                        stats = LaneStats(lane_id=i+1, vehicle_count=total, density=density_label)
                                        db.session.add(stats)
                                        
                                        # Also log the specific vehicle breakdown for Analytics pie chart
                                        for v_type, v_count in counts.items():
                                            if v_count > 0:
                                                v_log = VehicleLog(lane_id=i+1, vehicle_type=v_type, count=v_count)
                                                db.session.add(v_log)
                                                
                                        db.session.commit()
                                        
                                        if i == 3: # Update global timer
                                            self.last_db_log = current_time
                                except Exception as e:
                                    print(f"DB Log Error: {e}")

                        # -- DRAWING (Every Frame) --
                        # Draw Ambulances
                        for (ax1, ay1, ax2, ay2) in cached_boxes[i]['ambulance']:
                            cv2.rectangle(frame, (ax1, ay1), (ax2, ay2), (0, 0, 255), 3)
                            cv2.putText(frame, "AMBULANCE", (ax1, ay1 - 10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        
                        # Draw Vehicles
                        for box_data in cached_boxes[i]['vehicles']:
                            (vx1, vy1, vx2, vy2) = box_data['coords']
                            
                            # Don't draw over ambulance (Optional check)
                            is_ambu = False
                            for (ax1, ay1, ax2, ay2) in cached_boxes[i]['ambulance']:
                                if vx1 == ax1 and vy1 == ay1:
                                    is_ambu = True
                                    break
                            if is_ambu: continue

                            label = box_data['label']
                            color = box_data['color']
                            cv2.rectangle(frame, (vx1, vy1), (vx2, vy2), color, 2)
                            cv2.putText(frame, label, (vx1, vy1 - 10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                        
                        # Encode
                        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                        self.frame_data[i] = buffer.tobytes()
                except Exception as e:
                    print(f"Error in lane {i}: {e}")
                    continue

            # Update Signal Controller (Check if ANY lane has ambulance)
            # We check specific lanes. If Staggered, we might have stale data for 3 frames, which is fine (100ms lag)
            ambulance_lane = -1
            for lid, active in enumerate(self.ambulance_active):
                if active:
                    ambulance_lane = lid
                    break
            
            if current_signal_logic and (frame_count % DETECT_INTERVAL == 0):
                current_signal_logic.set_ambulance_event(ambulance_lane, ambulance_lane != -1)
            
            frame_count += 1
            
            # FPS Limiter
            elapsed = time.time() - start_time
            if elapsed < 0.033: # Target ~30 FPS
                time.sleep(0.033 - elapsed)

    def get_frame(self, lane_id):
        return self.frame_data.get(lane_id)
        
    def get_lane_count(self, lane_id):
        return self.lane_data[lane_id]['count']

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        for cap in self.caps:
            if cap:
                cap.release()
