import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    PROJECT_NAME: str = "YOLO-World Object Detection API"
    PROJECT_VERSION: str = "1.0.0"
    
    # Supabase Settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    
    # Database Settings
    # Standard format: postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Machine Learning Settings
    YOLO_MODEL_NAME: str = os.getenv("YOLO_MODEL_NAME", "yolov8s-worldv2.pt")
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))
    
    # Upload Directories
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    
    def __init__(self):
        # Create uploads directory if it doesn't exist
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
