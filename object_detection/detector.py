import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
from object_detection.utils import get_color_palette, draw_bounding_box

class ObjectDetector:
    def __init__(self, model_name="yolov8n.pt", conf_threshold=0.25):
        """
        Initializes the YOLOv8 model.
        
        Args:
            model_name (str): Name/path of the model weights (e.g. 'yolov8n.pt', 'yolov8s.pt').
            conf_threshold (float): Default confidence threshold for detection.
        """
        self.model_name = model_name
        self.conf_threshold = conf_threshold
        
        # Load pre-trained model. If weights aren't local, YOLO downloads them automatically.
        print(f"Loading object detection model: {model_name}...")
        self.model = YOLO(model_name)
        
        # Get names dictionary and generate a unique color palette
        self.names = self.model.names
        self.colors = get_color_palette(len(self.names))

    def detect(self, source, conf=None):
        """
        Runs object detection on the input image source (file path, numpy array, PIL Image).
        
        Args:
            source: Input source for YOLO model.
            conf (float): Custom confidence threshold (overrides default if provided).
            
        Returns:
            list[dict]: List of detection dictionaries, each containing:
                - class_id (int)
                - class_name (str)
                - confidence (float)
                - box (list[float]): Bounding box [xmin, ymin, xmax, ymax]
        """
        conf_val = conf if conf is not None else self.conf_threshold
        results = self.model.predict(source, conf=conf_val, verbose=False)
        
        detections = []
        if not results:
            return detections
            
        result = results[0]
        boxes = result.boxes
        if boxes is not None:
            for box in boxes:
                xyxy = box.xyxy[0].tolist()  # [xmin, ymin, xmax, ymax]
                score = float(box.conf[0])
                cls_id = int(box.cls[0])
                class_name = self.names.get(cls_id, "unknown")
                
                detections.append({
                    "class_id": cls_id,
                    "class_name": class_name,
                    "confidence": round(score, 4),
                    "box": [float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])]
                })
        return detections

    def annotate_frame(self, frame, detections):
        """
        Draws bounding boxes and labels for the list of detections onto the frame.
        
        Args:
            frame (numpy.ndarray): Frame/image to annotate.
            detections (list[dict]): Detections returned by the detect() method.
            
        Returns:
            numpy.ndarray: Annotated frame.
        """
        annotated_frame = frame.copy()
        for det in detections:
            cls_id = det["class_id"]
            class_name = det["class_name"]
            confidence = det["confidence"]
            box = det["box"]
            
            # Map class ID to color. If out of range, fallback to green.
            color = self.colors[cls_id] if cls_id < len(self.colors) else (0, 255, 0)
            
            # Draw box using the utility function
            annotated_frame = draw_bounding_box(annotated_frame, class_name, confidence, box, color)
            
        return annotated_frame
