from ultralytics import YOLO
import cv2
import numpy as np
import easyocr
import threading

class AmbulanceDetector:
    def __init__(self, model_path, confidence=0.6):
        self.use_heuristic = False
        try:
            # We use the heuristic mode primarily now as per user request
            # But we still need a detector to find the VEHICLES first
            self.model = YOLO('yolov8n.pt') 
            self.loaded = True
        except Exception as e:
            print(f"Error loading YOLO: {e}")
            self.loaded = False
        
        self.confidence = confidence
        
        # Initialize OCR Reader
        # This might download the model on first run
        print("Initializing EasyOCR... (this might take a moment)")
        try:
            self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            self.ocr_ready = True
            print("EasyOCR Initialized.")
        except Exception as e:
            print(f"Failed to load EasyOCR: {e}")
            self.ocr_ready = False

        self.target_keywords = {"AMBULANCE", "ECNALUBMA", "EMS", "PARAMEDIC", "108", "112", "EMERGENCY", "RESCUE"}

    def detect(self, frame):
        """
        Detect ambulances using OCR and Light Detection.
        Legacy method for standalone use.
        """
        # 1. Detect candidate vehicles (Car, Bus, Truck)
        results = self.model(frame, stream=True, verbose=False, conf=0.4, classes=[2, 5, 7])
        
        boxes = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                boxes.append((x1, y1, x2, y2))
                
        return self.check_boxes(frame, boxes)

    def check_boxes(self, frame, boxes):
        """
        Efficient check using existing bounding boxes.
        Returns: has_ambulance, annotated_frame, ambulance_boxes, verified_indices
        """
        ambulance_boxes = []
        verified_indices = [] # Indices of boxes that are ambulances
        has_ambulance = False
        annotated_frame = frame # Modify in place or copy if needed outside
        
        for i, (x1, y1, x2, y2) in enumerate(boxes):
            w, h = x2 - x1, y2 - y1
            
            if w < 60 or h < 60: continue

            roi = frame[y1:y2, x1:x2]
            if roi.size == 0: continue

            is_ambulance = False
            label = ""
            
            # A. LIGHT DETECTION (Fast)
            if self._detect_emergency_lights(roi):
                is_ambulance = True
                label = "AMBULANCE (LIGHTS)"
            
            # B. TEXT DETECTION (Slow, Optional)
            # Only run if not already found and OCR is ready
            # SKIP OCR for speed by default unless very confident candidate or requested
            # For now, let's keep it but maybe skip if roi is small
            elif not is_ambulance and self.ocr_ready and w > 120:
                # Limit OCR calls: only 1 per frame max? No, just rely on size
                if self._detect_text(roi):
                    is_ambulance = True
                    label = "AMBULANCE (TEXT)"
            
            if is_ambulance:
                has_ambulance = True
                ambulance_boxes.append((x1, y1, x2, y2))
                verified_indices.append(i)
                
                # Draw
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(annotated_frame, label, (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                            
        return has_ambulance, annotated_frame, ambulance_boxes

    def _detect_emergency_lights(self, roi):
        """
        Detect flashing Blue/Red lights.
        Focuses on the top half of the vehicle.
        """
        h, w = roi.shape[:2]
        # Crop top 40% (Light bars are usually on top)
        top_roi = roi[0:int(h*0.4), :]
        
        hsv = cv2.cvtColor(top_roi, cv2.COLOR_BGR2HSV)
        
        # 1. BLUE LIGHTS (High Saturation, High Value)
        # H: 100-140 (Blue)
        lower_blue = np.array([100, 180, 180]) # Very filtered
        upper_blue = np.array([140, 255, 255])
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # 2. RED LIGHTS (High Brightness Red)
        # Intense red lights often appear orange/yellowish in center if blown out, 
        # but the rim is red. simple red mask:
        lower_red1 = np.array([0, 180, 200])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 180, 200])
        upper_red2 = np.array([180, 255, 255])
        mask_red = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)
        
        blue_count = cv2.countNonZero(mask_blue)
        red_count = cv2.countNonZero(mask_red)
        
        # Threshold: Needs a cluster of pixels (e.g. > 20 pixels)
        # This avoids noise pixels
        has_blue = blue_count > 20
        has_red = red_count > 20
        
        return has_blue or has_red

    def _detect_text(self, roi):
        """
        Run OCR on the ROI. 
        """
        try:
            # Preprocess for OCR: Grayscale + Contrast
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            # Maybe histogram equalization?
            # gray = cv2.equalizeHist(gray)
            
            # Read text
            results = self.reader.readtext(gray, detail=0)
            
            for text in results:
                clean_text = text.upper().replace(" ", "")
                # Check exact or partial matches
                for key in self.target_keywords:
                    # Simple fuzzy: is key in text?
                    if key in clean_text:
                        # Debug
                        print(f"OCR Match: {key} in {clean_text}")
                        return True
                    
                    # Handle Levenshtein? No, too slow/complex. 
                    # "ECNALUBMA" is unique enough.
                    
            return False
        except Exception as e:
            print(f"OCR Error: {e}")
            return False
