import logging
from pathlib import Path
from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Supabase client with Service Role Key for backend administration
supabase_client: Client = None

if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Supabase Admin client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
else:
    logger.warning("Supabase credentials missing. Supabase Storage uploads will be disabled or fall back to local mocks.")

def upload_file(local_path: str, storage_path: str, content_type: str = "image/jpeg") -> str:
    """
    Uploads a local file to Supabase Storage and returns its public URL.
    Args:
         local_path: Path to the local file.
         storage_path: Target path inside the 'object-detection' bucket (e.g. 'user_id/original_image.jpg').
         content_type: MIME type of the file.
    Returns:
         The public URL of the uploaded file.
    """
    if supabase_client is None:
        # Fallback for development if Supabase is not connected
        logger.warning(f"Mocking upload for {local_path} to {storage_path}")
        return f"http://localhost:8000/uploads/{Path(local_path).name}"
        
    try:
        path_obj = Path(local_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")
            
        with open(local_path, "rb") as f:
            file_data = f.read()
            
        # Upload file to 'object-detection' bucket
        # We use upsert=True in case we overwrite or retry
        bucket_name = "object-detection"
        
        logger.info(f"Uploading {local_path} to Supabase bucket '{bucket_name}' path: {storage_path}")
        response = supabase_client.storage.from_(bucket_name).upload(
            path=storage_path,
            file=file_data,
            file_options={"content-type": content_type, "x-upsert": "true"}
        )
        
        # Get public URL
        public_url = supabase_client.storage.from_(bucket_name).get_public_url(storage_path)
        logger.info(f"File uploaded successfully. Public URL: {public_url}")
        return public_url
        
    except Exception as e:
        logger.error(f"Failed to upload file to Supabase: {str(e)}")
        raise e

def delete_file(storage_path: str) -> bool:
    """
    Deletes a file from the 'object-detection' bucket in Supabase Storage.
    """
    if supabase_client is None:
        logger.warning(f"Mocking delete for path {storage_path}")
        return True
        
    try:
        bucket_name = "object-detection"
        logger.info(f"Deleting path {storage_path} from Supabase bucket '{bucket_name}'")
        supabase_client.storage.from_(bucket_name).remove([storage_path])
        return True
    except Exception as e:
        logger.error(f"Failed to delete file from Supabase storage: {str(e)}")
        return False
