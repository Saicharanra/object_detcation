from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
import logging

from app.database.session import get_db
from app.api.auth import get_current_user
from app.services.detection_service import process_detection, delete_detection_history
from app.models.db_models import UploadedImage, Detection

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Object Detection"])

# Max file size limit: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024 
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def validate_image(file: UploadFile):
    # Check file extension
    import os
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    # Check content type header
    if not file.content_type.startswith("image/"):
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not an image"
         )

@router.post("/detect")
async def detect_objects(
    file: UploadFile = File(...),
    prompt: str = Form(None, description="Comma-separated list of items to detect (e.g. 'laptop, dog, red cup')"),
    confidence: float = Form(None, description="Confidence threshold override"),
    use_custom_model: bool = Form(False, description="Whether to use the custom fine-tuned model weights"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an image and detect objects using open-vocabulary YOLO-World.
    Saves the image and detections to Supabase and PostgreSQL.
    """
    validate_image(file)
    try:
        # Process detection
        res = process_detection(
            db=db,
            user_id=current_user["id"],
            file=file,
            prompt=prompt,
            confidence_threshold=confidence,
            use_custom_model=use_custom_model
        )
        return res
    except Exception as e:
        logger.error(f"Error in /detect: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference and storage processing failed: {str(e)}"
        )

@router.post("/upload")
async def upload_and_detect(
    file: UploadFile = File(...),
    prompt: str = Form(None),
    confidence: float = Form(None),
    use_custom_model: bool = Form(False),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Alias for /detect to align with the upload endpoint requirement.
    """
    return await detect_objects(
        file=file,
        prompt=prompt,
        confidence=confidence,
        use_custom_model=use_custom_model,
        current_user=current_user,
        db=db
    )

@router.get("/history")
def get_history(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str = Query(None, description="Search detections by object name"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the authenticated user's detection history, including bounding box details.
    Allows searching by object name.
    """
    user_id = current_user["id"]
    
    query = db.query(UploadedImage).filter(UploadedImage.user_id == user_id)
    
    if search:
        # Filter images that have detections matching the search text
        query = query.join(UploadedImage.detections).filter(
            Detection.object_name.ilike(f"%{search}%")
        ).distinct()
        
    total_count = query.count()
    images = query.order_by(UploadedImage.uploaded_at.desc()).offset(offset).limit(limit).all()
    
    history_list = []
    for img in images:
        detections = []
        for det in img.detections:
            # If search is present, we still return all detections for this image, 
            # or optionally filter them, returning all is standard.
            detections.append({
                "id": det.id,
                "name": det.object_name,
                "confidence": det.confidence,
                "bounding_box": {
                    "xmin": det.x_min,
                    "ymin": det.y_min,
                    "xmax": det.x_max,
                    "ymax": det.y_max
                },
                "prompt_used": det.prompt_used,
                "processing_time": f"{det.processing_time:.2f}s"
            })
            
        history_list.append({
            "image_id": img.id,
            "original_filename": img.original_filename,
            "image_url": img.image_url,
            "annotated_image_url": img.annotated_image_url,
            "uploaded_at": img.uploaded_at.isoformat(),
            "detections": detections
        })
        
    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "history": history_list
    }

@router.delete("/history/{id}")
def delete_history_item(
    id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes an upload from the user's history and cleans up storage.
    """
    success = delete_detection_history(db, current_user["id"], id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found or access denied"
        )
    return {"status": "success", "message": "Detection history item deleted successfully"}
