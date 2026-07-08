import os
import uuid
import logging
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Load backend/.env to read Supabase configuration
ENV_PATH = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

supabase_client: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully.")
    except Exception as e:
        print(f"Error initializing Supabase client: {str(e)}")
else:
    print("Warning: Supabase credentials missing from backend/.env. Supabase integration will be disabled.")

def upload_file_to_supabase(local_path: str, storage_path: str, content_type: str = "image/jpeg") -> str:
    """
    Uploads a local file to the 'object-detection' Supabase storage bucket.
    
    Args:
        local_path (str): Absolute or relative path to the local file.
        storage_path (str): Remote path inside the bucket (e.g., 'user_id/image.jpg').
        content_type (str): MIME type of the file.
        
    Returns:
        str: Public URL of the uploaded file.
    """
    if not supabase_client:
        raise ValueError("Supabase client is not initialized.")
        
    bucket_name = "object-detection"
    path_obj = Path(local_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Local file not found: {local_path}")
        
    with open(local_path, "rb") as f:
        file_data = f.read()
        
    # Upload to 'object-detection' bucket using x-upsert to allow overwriting on conflict
    supabase_client.storage.from_(bucket_name).upload(
        path=storage_path,
        file=file_data,
        file_options={"content-type": content_type, "x-upsert": "true"}
    )
    
    # Retrieve public URL
    public_url = supabase_client.storage.from_(bucket_name).get_public_url(storage_path)
    return public_url

def save_to_supabase(
    user_id: str,
    original_filename: str,
    local_orig_path: str,
    local_annot_path: str,
    detections: list[dict],
    processing_time: float
) -> dict:
    """
    Uploads original and annotated frames to Supabase storage,
    and inserts records into the 'uploaded_images' and 'detections' tables.
    
    Args:
        user_id (str): User ID (UUID) associated with the records.
        original_filename (str): Name of the source file.
        local_orig_path (str): Local path of the original image.
        local_annot_path (str): Local path of the annotated image.
        detections (list[dict]): List of detection dicts containing 'class_name', 'confidence', 'box'.
        processing_time (float): Detection latency in seconds.
        
    Returns:
        dict: Upload result details including image ID and public URLs.
    """
    if not supabase_client:
        raise ValueError("Supabase client is not initialized. Check your credentials.")
        
    image_uuid = str(uuid.uuid4())
    file_ext = Path(original_filename).suffix or ".jpg"
    
    # 1. Upload original image
    # Path format: {user_id}/{image_uuid}_original{ext}
    storage_orig_path = f"{user_id}/{image_uuid}_original{file_ext}"
    orig_url = upload_file_to_supabase(local_orig_path, storage_orig_path)
    
    # 2. Upload annotated image
    # Path format: {user_id}/{image_uuid}_annotated{ext}
    storage_annot_path = f"{user_id}/{image_uuid}_annotated{file_ext}"
    annot_url = upload_file_to_supabase(local_annot_path, storage_annot_path)
    
    # 3. Insert into public.uploaded_images table
    image_record = {
        "id": image_uuid,
        "user_id": user_id,
        "image_url": orig_url,
        "annotated_image_url": annot_url,
        "original_filename": original_filename
    }
    
    supabase_client.table("uploaded_images").insert(image_record).execute()
    
    # 4. Insert into public.detections table
    detection_records = []
    for det in detections:
        box = det["box"]
        detection_records.append({
            "id": str(uuid.uuid4()),
            "image_id": image_uuid,
            "object_name": det["class_name"],
            "confidence": det["confidence"],
            "x_min": box[0],
            "y_min": box[1],
            "x_max": box[2],
            "y_max": box[3],
            "processing_time": processing_time
        })
        
    if detection_records:
        supabase_client.table("detections").insert(detection_records).execute()
        
    return {
        "image_id": image_uuid,
        "image_url": orig_url,
        "annotated_image_url": annot_url,
        "detections_count": len(detection_records)
    }
