from fastapi import APIRouter, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session
import logging
from pathlib import Path

from app.database.session import get_db
from app.api.auth import get_current_user
from app.services.training_service import trigger_training
from app.models.db_models import TrainingJob, UploadedImage
from app.ml.yolo_model import yolo_model

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/train", tags=["Model Training"])

@router.post("")
def start_model_training(
    epochs: int = Form(5, ge=1, le=20, description="Number of training epochs (max 20)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers a background training/fine-tuning run on the user's annotated images.
    """
    user_id = current_user["id"]
    
    # Check if a training job is already running
    active_job = db.query(TrainingJob).filter(
        TrainingJob.user_id == user_id,
        TrainingJob.status.in_(["pending", "training"])
    ).first()
    
    if active_job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A training job is already in progress. Please wait for it to complete."
        )
        
    try:
        # Unload any currently cached model to prepare for the new weights
        yolo_model.unload_custom_model(user_id)
        
        # Trigger training
        res = trigger_training(db, user_id, epochs)
        return {
            "status": "success",
            "message": "Training job queued successfully.",
            "job": res
        }
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        logger.error(f"Failed to start training: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger training run: {str(e)}"
        )

@router.get("/status")
def get_training_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the latest training job status and whether a custom model is available.
    """
    user_id = current_user["id"]
    
    latest_job = db.query(TrainingJob).filter(
        TrainingJob.user_id == user_id
    ).order_by(TrainingJob.created_at.desc()).first()
    
    weights_path = Path(__file__).resolve().parent.parent / "ml" / "weights" / user_id / "best.pt"
    custom_model_available = weights_path.exists()
    
    trained_classes = []
    metadata_path = Path(__file__).resolve().parent.parent / "ml" / "weights" / user_id / "metadata.json"
    if metadata_path.exists():
        import json
        try:
            with open(metadata_path, "r") as mf:
                meta = json.load(mf)
                trained_classes = meta.get("classes", [])
        except Exception as ex:
            logger.warning(f"Could not read metadata for user {user_id}: {str(ex)}")
            
    res = {
        "custom_model_available": custom_model_available,
        "trained_classes": trained_classes,
        "latest_job": None
    }
    
    if latest_job:
        res["latest_job"] = {
            "id": latest_job.id,
            "status": latest_job.status,
            "epochs": latest_job.epochs,
            "trained_classes": latest_job.trained_classes,
            "error_message": latest_job.error_message,
            "created_at": latest_job.created_at.isoformat(),
            "completed_at": latest_job.completed_at.isoformat() if latest_job.completed_at else None
        }
        
    return res

@router.get("/classes")
def get_classes_for_training(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns unique classes present in the user's detection history, along with suitability for training.
    """
    user_id = current_user["id"]
    
    images = db.query(UploadedImage).filter(UploadedImage.user_id == user_id).all()
    annotated_images = [img for img in images if len(img.detections) > 0]
    
    all_classes = set()
    for img in annotated_images:
        for det in img.detections:
            all_classes.add(det.object_name.strip())
            
    classes_list = sorted(list(all_classes))
    
    return {
        "classes": classes_list,
        "images_count": len(annotated_images),
        "can_train": len(annotated_images) >= 3,
        "min_images_required": 3
    }
