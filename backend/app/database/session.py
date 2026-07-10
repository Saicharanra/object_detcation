from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# If DATABASE_URL is not set, we can fall back to sqlite for development,
# but since Supabase PostgreSQL is required, we ensure DATABASE_URL is utilized.
DATABASE_URL = settings.DATABASE_URL
if not DATABASE_URL:
    # Fallback to local sqlite database for local development if not provided
    DATABASE_URL = "sqlite:///./sql_app.db"

# Create engine
# Using connect_args={"check_same_thread": False} only for sqlite
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
