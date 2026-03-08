import cv2
import threading
import time
from backend.cv.vehicle_detector import VehicleDetector
from backend.cv.ambulance_detector import AmbulanceDetector
from backend.cv.traffic_logic import TrafficLogic
from backend.database.models import LaneStats, VehicleLog, AmbulanceEvent
from backend.database.database import SessionLocal

class VideoProcessor:
    def __init__(self, config, signal_controller=None):
        self.config = config
        self.signal_controller = signal_controller
        
        self.vehicle_detector = VehicleDetector(config.MODEL_VEHICLE_PATH)
        self.ambulance_detector = AmbulanceDetector(config.MODEL_AMBULANCE_PATH)
        self.traffic_logic = TrafficLogic(config)
        
        # Store latest processing results
        self.frame_data = {} # {0: frame, 1: frame, ...}
        self.lane_data = {i: {'count': 0, 'density': 'Low', 'details': {}} for i in range(4)}
        self.ambulance_active = [False] * 4 # Track ambulance state per lane
        
        self.caps = [None] * 4
        self.sources = [None] * 4 # Paths to video files
        
        self.running = False
        self.thread = None
        self.last_db_log = 0  # Timestamp of last DB write

    def start_streams(self, video_paths):
        """
        Initialize video captures
        video_paths: list of 4 file paths or stream URLs
        """
        if self.running or (self.thread and self.thread.is_alive()):
            self.stop()
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
        DETECT_INTERVAL = 4 
        frame_count = 0
        
        cached_boxes = {i: {'vehicles': [], 'ambulance': []} for i in range(4)}
        
        while self.running:
            start_time = time.time()
            
            for i in range(4):
                try:
                    if self.caps[i] and self.caps[i].isOpened():
                        ret, raw_frame = self.caps[i].read()
                        if not ret:
                            print(f"Lane {i}: Stream ended or disconnected.")
                            self.caps[i].release()
                            self.caps[i] = None
                            continue
                            
                        frame = cv2.resize(raw_frame, (480, 270))
                        
                        if (frame_count + i) % DETECT_INTERVAL == 0:
                            _, counts, total, veh_data_list = self.vehicle_detector.detect(frame, draw=False)
                            raw_boxes = [v['coords'] for v in veh_data_list]
                            has_ambu, _, ambu_boxes = self.ambulance_detector.check_boxes(frame, raw_boxes)
                            
                            self.ambulance_active[i] = has_ambu
                            cached_boxes[i]['ambulance'] = ambu_boxes
                            cached_boxes[i]['vehicles'] = veh_data_list

                            self.lane_data[i]['count'] = total
                            self.lane_data[i]['details'] = counts 
                            density_label = self.traffic_logic.get_density_label(total)
                            self.lane_data[i]['density'] = density_label
                            
                            current_time = time.time()
                            if self.last_db_log + 5 < current_time:
                                db = SessionLocal()
                                try:
                                    stats = LaneStats(lane_id=i+1, vehicle_count=total, density=density_label)
                                    db.add(stats)
                                    
                                    for v_type, v_count in counts.items():
                                        if v_count > 0:
                                            v_log = VehicleLog(lane_id=i+1, vehicle_type=v_type, count=v_count)
                                            db.add(v_log)
                                            
                                    db.commit()
                                    self.last_db_log = current_time
                                except Exception as e:
                                    db.rollback()
                                    print(f"DB Log Error: {e}")
                                finally:
                                    db.close()

                        for (ax1, ay1, ax2, ay2) in cached_boxes[i]['ambulance']:
                            cv2.rectangle(frame, (ax1, ay1), (ax2, ay2), (0, 0, 255), 3)
                            cv2.putText(frame, "AMBULANCE", (ax1, ay1 - 10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        
                        for box_data in cached_boxes[i]['vehicles']:
                            (vx1, vy1, vx2, vy2) = box_data['coords']
                            
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
                        
                        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                        self.frame_data[i] = buffer.tobytes()
                except Exception as e:
                    print(f"Error in lane {i}: {e}")
                    continue

            ambulance_lane = -1
            for lid, active in enumerate(self.ambulance_active):
                if active:
                    ambulance_lane = lid
                    break
            
            if self.signal_controller and (frame_count % DETECT_INTERVAL == 0):
                self.signal_controller.set_ambulance_event(ambulance_lane, ambulance_lane != -1)
            
            frame_count += 1
            
            elapsed = time.time() - start_time
            if elapsed < 0.033:
                time.sleep(0.033 - elapsed)

    def get_frame(self, lane_id):
        return self.frame_data.get(lane_id)
        
    def get_lane_count(self, lane_id):
        return self.lane_data[lane_id]['count']

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        for cap in self.caps:
            if cap:
                cap.release()
        self.caps = [None] * 4
