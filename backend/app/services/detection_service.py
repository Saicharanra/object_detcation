import os
import uuid
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.config import settings
from app.ml.yolo_model import yolo_model
from app.services.supabase_storage import upload_file, delete_file
from app.models.db_models import UploadedImage, Detection

logger = logging.getLogger(__name__)

def process_detection(
    db: Session,
    user_id: str,
    file: UploadFile,
    prompt: str = None,
    confidence_threshold: float = None,
    use_custom_model: bool = False
) -> dict:
    """
    Processes object detection for an uploaded image.
    Steps:
      1. Save uploaded file to local temp directory.
      2. Upload original file to Supabase Storage.
      3. Run YOLO-World detection (using prompt list if provided).
      4. Upload annotated file to Supabase Storage.
      5. Save records into 'uploaded_images' and 'detections' tables.
      6. Remove local temporary files.
      7. Return results.
    """
    temp_orig_path = None
    temp_annot_path = None
    image_uuid = str(uuid.uuid4())
    
    try:
        # Determine extension
        original_filename = file.filename
        file_ext = Path(original_filename).suffix
        if not file_ext:
            # Default to .jpg if no extension
            file_ext = ".jpg"
            
        # 1. Save uploaded file locally
        temp_orig_filename = f"{image_uuid}_original{file_ext}"
        temp_orig_path = settings.UPLOAD_DIR / temp_orig_filename
        
        with open(temp_orig_path, "wb") as f:
            f.write(file.file.read())
            
        # Determine MIME type
        content_type = file.content_type or "image/jpeg"
        
        # 2. Upload original file to Supabase Storage
        # Format: {user_id}/{image_uuid}_original{ext}
        storage_orig_path = f"{user_id}/{image_uuid}_original{file_ext}"
        original_url = upload_file(str(temp_orig_path), storage_orig_path, content_type)
        
        # 3. Parse custom prompts (comma-separated list, e.g. "laptop, red bottle, keyboard")
        custom_classes = None
        if prompt:
            custom_classes = [c.strip() for c in prompt.split(",") if c.strip()]
            
        # Run YOLO-World Inference
        detections_list, processing_time, local_annotated_path = yolo_model.predict(
            image_path=str(temp_orig_path),
            custom_classes=custom_classes,
            confidence=confidence_threshold,
            user_id=user_id,
            use_custom_model=use_custom_model
        )
        temp_annot_path = Path(local_annotated_path)
        
        # 4. Upload annotated file to Supabase Storage
        storage_annot_path = f"{user_id}/{image_uuid}_annotated{file_ext}"
        annotated_url = upload_file(str(temp_annot_path), storage_annot_path, content_type)
        
        # 5. Insert records in Database
        # 5a. Create UploadedImage record
        db_image = UploadedImage(
            id=image_uuid,
            user_id=user_id,
            image_url=original_url,
            annotated_image_url=annotated_url,
            original_filename=original_filename
        )
        db.add(db_image)
        db.flush() # Flush to get primary key link active if needed (already set explicitly)
        
        # 5b. Create Detection records
        for det in detections_list:
            bbox = det["bounding_box"]
            db_det = Detection(
                id=str(uuid.uuid4()),
                image_id=image_uuid,
                object_name=det["name"],
                confidence=det["confidence"],
                x_min=bbox["xmin"],
                y_min=bbox["ymin"],
                x_max=bbox["xmax"],
                y_max=bbox["ymax"],
                prompt_used=prompt,
                processing_time=processing_time
            )
            db.add(db_det)
            
        db.commit()
        
        # Format and return JSON response
        formatted_objects = [
            {
                "name": det["name"],
                "confidence": det["confidence"],
                "bounding_box": det["bounding_box"]
            }
            for det in detections_list
        ]
        
        return {
            "image_id": image_uuid,
            "original_image_url": original_url,
            "annotated_image_url": annotated_url,
            "processing_time": f"{processing_time:.2f}s",
            "objects": formatted_objects
        }
        
    except Exception as e:
        if db:
            db.rollback()
        logger.error(f"Error processing detection: {str(e)}", exc_info=True)
        raise e
        
    finally:
        # 6. Cleanup temporary files from disk
        if temp_orig_path and temp_orig_path.exists():
            try:
                os.remove(temp_orig_path)
            except Exception as ex:
                logger.warning(f"Could not remove temp original file: {str(ex)}")
                
        if temp_annot_path and temp_annot_path.exists():
            try:
                os.remove(temp_annot_path)
            except Exception as ex:
                logger.warning(f"Could not remove temp annotated file: {str(ex)}")

def delete_detection_history(db: Session, user_id: str, image_id: str) -> bool:
    """
    Deletes the uploaded image and its detections from the database and storage.
    Only allows deletion if the image belongs to the requested user.
    """
    try:
        # Retrieve image record and verify ownership
        db_image = db.query(UploadedImage).filter(
            UploadedImage.id == image_id, 
            UploadedImage.user_id == user_id
        ).first()
        
        if not db_image:
            return False
            
        # Parse storage paths from URLs
        # URL structure: https://[project-id].supabase.co/storage/v1/object/public/object-detection/{user_id}/{image_uuid}_original.{ext}
        # We can extract the relative path by looking at the suffix after the bucket name
        bucket_prefix = "/object-detection/"
        
        def extract_storage_path(url: str) -> str:
            if bucket_prefix in url:
                return url.split(bucket_prefix)[-1]
            # Fallback if URL layout is different
            return url.split("/")[-2] + "/" + url.split("/")[-1]
            
        try:
            if db_image.image_url:
                delete_file(extract_storage_path(db_image.image_url))
            if db_image.annotated_image_url:
                delete_file(extract_storage_path(db_image.annotated_image_url))
        except Exception as e:
            logger.warning(f"Failed to delete files from storage: {str(e)}")
            
        # Delete from database (cascade will handle detections and triggers will update analytics)
        db.delete(db_image)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting detection history: {str(e)}")
        raise e
