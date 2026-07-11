import time
import logging
from pathlib import Path
from PIL import Image
import cv2
import numpy as np
from ultralytics import YOLO, YOLOWorld
from app.config import settings

logger = logging.getLogger(__name__)

class YoloWorldModel:
    def __init__(self):
        self.model = None          # Fast YOLOv8/v11 model for streaming (e.g. yolo11n.pt)
        self.world_model = None    # YOLO-World open-vocabulary model for Detection Studio (e.g. yolov8s-worldv2.pt)
        self.custom_models = {}    # dict mapping user_id -> YOLO instance
        self.default_classes = [
            "laptop", "mobile phone", "keyboard", "mouse", "water bottle", 
            "car", "dog", "bicycle", "person", "helmet", "chair", 
            "backpack", "coffee mug", "glasses", "cup", "book"
        ]

    def load_model(self):
        """Loads the standard fast model (yolo11n.pt) for real-time WebSocket streaming."""
        if self.model is None:
            # We use yolo11n.pt for fast streaming
            model_name = "yolo11n.pt"
            logger.info(f"Loading fast YOLO model for stream: {model_name}...")
            start_time = time.time()
            self.model = YOLO(model_name)
            logger.info(f"Fast YOLO model loaded in {time.time() - start_time:.2f} seconds.")

    def load_world_model(self):
        """Loads the YOLO-World open-vocabulary model (yolov8s-worldv2.pt) for Detection Studio."""
        if self.world_model is None:
            model_name = "yolov8s-worldv2.pt"
            logger.info(f"Loading YOLO-World open-vocabulary model: {model_name}...")
            start_time = time.time()
            self.world_model = YOLOWorld(model_name)
            logger.info(f"YOLO-World model loaded in {time.time() - start_time:.2f} seconds.")

    def load_custom_model(self, user_id: str) -> YOLO:
        if user_id not in self.custom_models:
            weights_path = Path(__file__).resolve().parent / "weights" / user_id / "best.pt"
            if weights_path.exists():
                logger.info(f"Loading custom YOLOv8 model for user {user_id}...")
                start_time = time.time()
                self.custom_models[user_id] = YOLO(str(weights_path))
                logger.info(f"Custom YOLOv8 model loaded in {time.time() - start_time:.2f} seconds.")
            else:
                logger.warning(f"Custom weights not found at {weights_path}, falling back to base model.")
                self.load_model()
                return self.model
        return self.custom_models[user_id]

    def unload_custom_model(self, user_id: str):
        if user_id in self.custom_models:
            del self.custom_models[user_id]
            logger.info(f"Unloaded custom model cache for user {user_id}.")

    def predict(
        self, 
        image_path: str, 
        custom_classes: list[str] = None, 
        confidence: float = None,
        user_id: str = None,
        use_custom_model: bool = False
    ) -> tuple[list[dict], float, str]:
        """
        Runs object detection on the image using YOLOv8 or YOLO-World.
        Returns:
            detections: List of dicts with object name, confidence, and bounding box coordinates.
            processing_time: Time taken in seconds.
            annotated_image_path: Path to the locally saved annotated image.
        """
        # Determine model
        if use_custom_model and user_id:
            weights_path = Path(__file__).resolve().parent / "weights" / user_id / "best.pt"
            if weights_path.exists():
                model_to_use = self.load_custom_model(user_id)
                # Load custom classes if present in metadata.json
                metadata_path = Path(__file__).resolve().parent / "weights" / user_id / "metadata.json"
                if metadata_path.exists():
                    import json
                    try:
                        with open(metadata_path, "r") as mf:
                            meta = json.load(mf)
                            classes_filter = meta.get("classes", [])
                    except Exception as ex:
                        logger.warning(f"Failed to read custom model metadata: {str(ex)}")
                        classes_filter = custom_classes
                else:
                    classes_filter = custom_classes
            else:
                self.load_world_model()
                model_to_use = self.world_model
                classes_filter = custom_classes
        else:
            self.load_world_model()
            model_to_use = self.world_model
            classes_filter = custom_classes

        conf = confidence if confidence is not None else settings.CONFIDENCE_THRESHOLD
        
        is_world_model = isinstance(model_to_use, YOLOWorld)
        if is_world_model:
            # Set the custom classes dynamically on YOLO-World
            if classes_filter:
                model_to_use.set_classes(classes_filter)
            else:
                model_to_use.set_classes(self.default_classes)

        # Run inference
        start_time = time.time()
        results = model_to_use.predict(image_path, conf=conf, verbose=False)
        processing_time = time.time() - start_time
        
        # Process results
        detections = []
        result = results[0]
        boxes = result.boxes
        
        # Determine filtering list (post-filter only for standard closed-vocabulary models)
        filter_list = None
        if classes_filter and not is_world_model:
            filter_list = [c.lower().strip() for c in classes_filter if c.strip()]
        
        for box in boxes:
            xyxy = box.xyxy[0].tolist()
            score = float(box.conf[0])
            cls_id = int(box.cls[0])
            
            # Map class ID to class name
            class_name = model_to_use.names[cls_id] if cls_id < len(model_to_use.names) else "unknown"
            
            # Class filter check (since standard YOLOv8 is closed vocabulary, we post-filter)
            if filter_list and class_name.lower().strip() not in filter_list:
                continue
                
            detections.append({
                "name": class_name.capitalize(),
                "confidence": round(score, 4),
                "bounding_box": {
                    "xmin": float(xyxy[0]),
                    "ymin": float(xyxy[1]),
                    "xmax": float(xyxy[2]),
                    "ymax": float(xyxy[3])
                }
            })
            
        # Draw bounding boxes and save annotated image
        annotated_img = result.plot()
        
        # Save locally in temp directory
        p = Path(image_path)
        annotated_image_path = str(p.parent / f"annotated_{p.name}")
        cv2.imwrite(annotated_image_path, annotated_img)
        
        return detections, processing_time, annotated_image_path

    def predict_frame(
        self, 
        frame: np.ndarray, 
        custom_classes: list[str] = None, 
        confidence: float = None,
        user_id: str = None,
        use_custom_model: bool = False
    ) -> tuple[list[dict], float, np.ndarray]:
        """
        Runs object detection on a single BGR numpy frame.
        Returns:
            detections: List of dicts with object name, confidence, and bounding box coordinates.
            processing_time: Time taken in seconds.
            annotated_frame: Processed numpy BGR frame with annotated bounding boxes.
        """
        # Determine model
        if use_custom_model and user_id:
            model_to_use = self.load_custom_model(user_id)
            classes_filter = custom_classes
        else:
            self.load_model()
            model_to_use = self.model
            classes_filter = custom_classes

        conf = confidence if confidence is not None else settings.CONFIDENCE_THRESHOLD
        
        is_world_model = isinstance(model_to_use, YOLOWorld)
        if is_world_model:
            if classes_filter:
                model_to_use.set_classes(classes_filter)
            else:
                model_to_use.set_classes(self.default_classes)

        # Run inference on the in-memory numpy array
        start_time = time.time()
        results = model_to_use.predict(frame, conf=conf, verbose=False)
        processing_time = time.time() - start_time
        
        # Process results
        detections = []
        result = results[0]
        boxes = result.boxes
        
        # Determine filtering list (post-filter only for standard closed-vocabulary models)
        filter_list = None
        if classes_filter and not is_world_model:
            filter_list = [c.lower().strip() for c in classes_filter if c.strip()]
        
        for box in boxes:
            xyxy = box.xyxy[0].tolist()
            score = float(box.conf[0])
            cls_id = int(box.cls[0])
            
            # Map class ID to class name
            class_name = model_to_use.names[cls_id] if cls_id < len(model_to_use.names) else "unknown"
            
            # Class filter check
            if filter_list and class_name.lower().strip() not in filter_list:
                continue
                
            detections.append({
                "name": class_name.capitalize(),
                "confidence": round(score, 4),
                "bounding_box": {
                    "xmin": float(xyxy[0]),
                    "ymin": float(xyxy[1]),
                    "xmax": float(xyxy[2]),
                    "ymax": float(xyxy[3])
                }
            })
            
        # Draw bounding boxes and return annotated image array
        annotated_img = result.plot()
        return detections, processing_time, annotated_img

# Global model instance
yolo_model = YoloWorldModel()
