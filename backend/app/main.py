from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database.session import engine, Base
import app.models.db_models  # Ensure all SQLAlchemy models are registered with Base.metadata before create_all
from app.api import auth, detection, analytics, training

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Create tables in the database (primarily for SQLite fallback, Supabase is run via schema.sql)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")
except Exception as e:
    logger.error(f"Failed to initialize database tables: {str(e)}")

# Modern Lifespan context manager for startup and shutdown actions
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Intentionally not eager-loading any model here: on a 1GB memory-capped host,
    # every model held in memory before it's actually needed is wasted headroom.
    # yolo11n.pt (predict_frame, live-stream) and yolov8s-worldv2.pt (predict, /detect)
    # both already lazy-load themselves on first use via YoloWorldModel.load_model()
    # / load_world_model().
    logger.info("Application starting up...")
    yield
    logger.info("Application shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    description="Production-ready FastAPI backend for YOLO-World open-vocabulary object detection."
)

# CORS configuration
# Allows requests from Vite React default port 5173, plus common alternatives,
# plus any additional origins configured via the CORS_ORIGINS env var (comma-separated).
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]
extra_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
origins = list(dict.fromkeys(default_origins + extra_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local uploads directory as static files (useful for local development image access)
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(detection.router)
app.include_router(analytics.router)
app.include_router(training.router)

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "model": settings.YOLO_MODEL_NAME
    }
