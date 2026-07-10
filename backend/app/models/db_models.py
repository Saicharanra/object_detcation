import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id = Column(String, primary_key=True, index=True) # maps to Supabase auth.users.id
    email = Column(String, index=True)
    full_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    images = relationship("UploadedImage", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="user", uselist=False, cascade="all, delete-orphan")
    training_jobs = relationship("TrainingJob", back_populates="user", cascade="all, delete-orphan")


class UploadedImage(Base):
    __tablename__ = "uploaded_images"
    __table_args__ = {"schema": "public"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("public.users.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String, nullable=False)
    annotated_image_url = Column(String, nullable=True)
    original_filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="images")
    detections = relationship("Detection", back_populates="image", cascade="all, delete-orphan")


class Detection(Base):
    __tablename__ = "detections"
    __table_args__ = {"schema": "public"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    image_id = Column(String, ForeignKey("public.uploaded_images.id", ondelete="CASCADE"), nullable=False)
    object_name = Column(String, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    x_min = Column(Float, nullable=False)
    y_min = Column(Float, nullable=False)
    x_max = Column(Float, nullable=False)
    y_max = Column(Float, nullable=False)
    prompt_used = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    image = relationship("UploadedImage", back_populates="detections")


class Analytics(Base):
    __tablename__ = "analytics"
    __table_args__ = {"schema": "public"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("public.users.id", ondelete="CASCADE"), unique=True, nullable=False)
    total_images = Column(Integer, default=0, nullable=False)
    total_detections = Column(Integer, default=0, nullable=False)
    most_detected_object = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="analytics")


class TrainingJob(Base):
    __tablename__ = "training_jobs"
    __table_args__ = {"schema": "public"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("public.users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending", nullable=False)
    epochs = Column(Integer, default=5, nullable=False)
    trained_classes = Column(ARRAY(String), nullable=True)
    error_message = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="training_jobs")
