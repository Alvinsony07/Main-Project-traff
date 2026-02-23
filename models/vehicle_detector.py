from ultralytics import YOLO
import cv2

class VehicleDetector:
    def __init__(self, model_path, confidence=0.3):
        try:
            self.model = YOLO(model_path) 
        except Exception as e:
            print(f"Warning: Using yolov8n.pt default.")
            self.model = YOLO('yolov8n.pt')
            
        self.confidence = confidence
        self.target_classes = [1, 2, 3, 5, 7]
        self.class_names = {
            1: 'bicycle', 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'
        }

    def detect(self, frame, exclude_boxes=None, draw=True):
        if exclude_boxes is None:
            exclude_boxes = []
            
        results = self.model(frame, stream=True, verbose=False, conf=self.confidence)
        
        counts = {name: 0 for name in self.class_names.values()}
        total_count = 0
        vehicle_boxes = [] # List of (x1,y1,x2,y2, label, color)
        
        annotated_frame = frame
        
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                if cls_id in self.target_classes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Overlap Check
                    is_excluded = False
                    for (ex_x1, ex_y1, ex_x2, ex_y2) in exclude_boxes:
                        dx = min(x2, ex_x2) - max(x1, ex_x1)
                        dy = min(y2, ex_y2) - max(y1, ex_y1)
                        if (dx >= 0) and (dy >= 0):
                            if (dx * dy) > 0.5 * ((x2-x1)*(y2-y1)):
                                is_excluded = True
                                break
                    if is_excluded: continue

                    name = self.class_names[cls_id]
                    counts[name] += 1
                    total_count += 1
                    
                    conf = box.conf[0]
                    label = f"{name} {int(conf*100)}%"
                    color = (0, 255, 0)
                    
                    # Store box for potential caching
                    vehicle_boxes.append({'coords': (x1, y1, x2, y2), 'label': label, 'color': color, 'type': name})
                    
                    # Draw
                    if draw:
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(annotated_frame, label, (x1, y1 - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                                
        return annotated_frame, counts, total_count, vehicle_boxes
