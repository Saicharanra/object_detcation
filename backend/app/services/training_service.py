import os
import shutil
import logging
import urllib.request
import threading
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import cv2

from app.config import settings
from app.database.session import SessionLocal
from app.models.db_models import TrainingJob, UploadedImage, Detection
from ultralytics import YOLOWorld

logger = logging.getLogger(__name__)

def trigger_training(db: Session, user_id: str, epochs: int = 5) -> dict:
    """
    Triggers a background fine-tuning job for the user's custom images and annotations.
    """
    # 1. Fetch images and detections
    images = db.query(UploadedImage).filter(UploadedImage.user_id == user_id).all()
    
    # Filter only images that have at least one detection
    annotated_images = [img for img in images if len(img.detections) > 0]
    
    if len(annotated_images) < 3:
         raise ValueError("Minimum 3 annotated images are required to start model training.")
         
    # 2. Get unique classes
    all_classes = set()
    for img in annotated_images:
        for det in img.detections:
            all_classes.add(det.object_name.strip())
            
    classes_list = sorted(list(all_classes))
    if not classes_list:
        raise ValueError("No objects/annotations found to train on.")
        
    # 3. Create a pending TrainingJob record
    job = TrainingJob(
        user_id=user_id,
        status="pending",
        epochs=epochs,
        trained_classes=classes_list
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # 4. Prepare dataset directory in a separate folder
    dataset_path = settings.UPLOAD_DIR / f"dataset_{user_id}"
    images_dir = dataset_path / "images" / "train"
    labels_dir = dataset_path / "labels" / "train"
    
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate labels and download images
    try:
        for img in annotated_images:
            # Determine filename
            file_ext = Path(img.original_filename).suffix or ".jpg"
            local_img_path = images_dir / f"{img.id}{file_ext}"
            
            # Download original image
            urllib.request.urlretrieve(img.image_url, str(local_img_path))
            
            # Read dimensions to normalize coordinates
            cv_img = cv2.imread(str(local_img_path))
            if cv_img is None:
                logger.warning(f"Could not read downloaded image: {img.image_url}")
                continue
            h, w, _ = cv_img.shape
            
            # Write labels in YOLO format (class_id x_center y_center box_width box_height)
            label_file_path = labels_dir / f"{img.id}.txt"
            with open(label_file_path, "w") as lf:
                for det in img.detections:
                    class_idx = classes_list.index(det.object_name.strip())
                    
                    # Normalize bounding box
                    box_w = (det.x_max - det.x_min) / w
                    box_h = (det.y_max - det.y_min) / h
                    x_center = (det.x_min + det.x_max) / 2.0 / w
                    y_center = (det.y_min + det.y_max) / 2.0 / h
                    
                    # Ensure values are within [0, 1] range
                    box_w = max(0.0, min(1.0, box_w))
                    box_h = max(0.0, min(1.0, box_h))
                    x_center = max(0.0, min(1.0, x_center))
                    y_center = max(0.0, min(1.0, y_center))
                    
                    lf.write(f"{class_idx} {x_center:.6f} {y_center:.6f} {box_w:.6f} {box_h:.6f}\n")
                    
        # 5. Write dataset.yaml
        yaml_content = f"""path: {dataset_path.as_posix()}
train: images/train
val: images/train  # validation fallback (use train data if dataset is small)

names:
"""
        for idx, cls_name in enumerate(classes_list):
            yaml_content += f"  {idx}: {cls_name}\n"
            
        dataset_yaml_path = dataset_path / "dataset.yaml"
        with open(dataset_yaml_path, "w") as yf:
            yf.write(yaml_content)
            
    except Exception as e:
        # If dataset prep fails, clean up directories and fail the job
        if dataset_path.exists():
            shutil.rmtree(dataset_path)
        job.status = "failed"
        job.error_message = f"Dataset preparation failed: {str(e)}"
        db.commit()
        raise e
        
    # 6. Start training thread
    thread = threading.Thread(
        target=_run_training_background,
        args=(user_id, job.id, str(dataset_yaml_path), epochs, classes_list)
    )
    thread.daemon = True
    thread.start()
    
    return {
        "job_id": job.id,
        "status": "pending",
        "epochs": epochs,
        "classes": classes_list
    }

def _run_training_background(user_id: str, job_id: str, dataset_yaml_path: str, epochs: int, trained_classes: list[str]):
    """
    Background worker that runs YOLO-World training.
    """
    db = SessionLocal()
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    if not job:
        db.close()
        return
        
    dataset_path = Path(dataset_yaml_path).parent
    project_dir = settings.UPLOAD_DIR / f"runs_{user_id}"
    
    try:
        job.status = "training"
        db.commit()
        
        logger.info(f"Starting background training for job {job_id} ({epochs} epochs)...")
        
        # Load the base model
        # Uses yolov8s-worldv2.pt (standard config)
        model = YOLOWorld(settings.YOLO_MODEL_NAME)
        
        # Run training
        # We explicitly configure CPU training since GPU capability isn't guaranteed on all developer devices.
        # This keeps the environment robust.
        model.train(
            data=dataset_yaml_path,
            epochs=epochs,
            imgsz=640,
            project=str(project_dir),
            name="train",
            exist_ok=True,
            device="cpu",
            workers=0, # Thread safety in Python
            verbose=False
        )
        
        # Define destination paths for weights
        weights_dir = Path(__file__).resolve().parent.parent / "ml" / "weights" / user_id
        weights_dir.mkdir(parents=True, exist_ok=True)
        
        best_weights_path = project_dir / "train" / "weights" / "best.pt"
        if best_weights_path.exists():
            shutil.copy(best_weights_path, weights_dir / "best.pt")
            
            # Save a metadata file indicating classes mapping
            import json
            metadata = {
                "classes": trained_classes,
                "trained_at": datetime.utcnow().isoformat(),
                "epochs": epochs
            }
            with open(weights_dir / "metadata.json", "w") as mf:
                json.dump(metadata, mf)
                
            job.status = "completed"
        else:
            raise FileNotFoundError("YOLO training completed but best.pt weights file was not generated.")
            
        job.completed_at = func.now()
        db.commit()
        logger.info(f"Training job {job_id} completed successfully.")
        
    except Exception as e:
        logger.error(f"Training job {job_id} failed: {str(e)}", exc_info=True)
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        
    finally:
        # Clean up temp dataset and training folders to save disk space
        try:
            if dataset_path.exists():
                shutil.rmtree(dataset_path)
            if project_dir.exists():
                shutil.rmtree(project_dir)
        except Exception as ex:
            logger.warning(f"Failed to cleanup temp directories: {str(ex)}")
        db.close()
