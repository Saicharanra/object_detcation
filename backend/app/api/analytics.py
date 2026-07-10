from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, case
from datetime import datetime, timedelta, date
import logging

from app.database.session import get_db
from app.api.auth import get_current_user
from app.models.db_models import UploadedImage, Detection, Analytics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("")
def get_analytics_data(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetches aggregated analytics data for the dashboard:
    1. Overall stats (total uploads, detections, most detected object).
    2. Confidence score distribution (binned counts).
    3. Upload activity over the last 14 days (daily count).
    4. Top 10 detected objects with counts.
    """
    user_id = current_user["id"]
    
    # 1. Fetch live metrics from analytics table
    stats = db.query(Analytics).filter(Analytics.user_id == user_id).first()
    
    total_images = stats.total_images if stats else 0
    total_detections = stats.total_detections if stats else 0
    most_detected = stats.most_detected_object if stats else "None"
    
    # If the database trigger hasn't run yet or stats are empty, recalculate manually as a fallback
    if total_images == 0:
        total_images = db.query(UploadedImage).filter(UploadedImage.user_id == user_id).count()
        total_detections = db.query(Detection).join(UploadedImage).filter(UploadedImage.user_id == user_id).count()
        
        # Most detected
        most_det_query = db.query(
            Detection.object_name, 
            func.count(Detection.id).label("cnt")
        ).join(UploadedImage).filter(
            UploadedImage.user_id == user_id
        ).group_by(Detection.object_name).order_by(func.count(Detection.id).desc()).first()
        
        most_detected = most_det_query[0] if most_det_query else "None"
        
    # 2. Confidence Distribution Bins (0.2-1.0 range, steps of 0.1)
    confidence_bins = {
        "0.2-0.3": 0,
        "0.3-0.4": 0,
        "0.4-0.5": 0,
        "0.5-0.6": 0,
        "0.6-0.7": 0,
        "0.7-0.8": 0,
        "0.8-0.9": 0,
        "0.9-1.0": 0
    }
    
    bin_expression = case(
        (Detection.confidence < 0.3, "0.2-0.3"),
        (Detection.confidence < 0.4, "0.3-0.4"),
        (Detection.confidence < 0.5, "0.4-0.5"),
        (Detection.confidence < 0.6, "0.5-0.6"),
        (Detection.confidence < 0.7, "0.6-0.7"),
        (Detection.confidence < 0.8, "0.7-0.8"),
        (Detection.confidence < 0.9, "0.8-0.9"),
        else_="0.9-1.0"
    ).label("bin")
    
    bin_counts = db.query(
        bin_expression,
        func.count(Detection.id)
    ).join(UploadedImage).filter(
        UploadedImage.user_id == user_id
    ).group_by("bin").all()
    
    for bin_name, count in bin_counts:
        if bin_name in confidence_bins:
            confidence_bins[bin_name] = count

    # 3. Upload Activity over last 14 days
    today = date.today()
    start_date = today - timedelta(days=13) # 14 days total including today
    
    # Generate list of last 14 days
    date_list = [start_date + timedelta(days=x) for x in range(14)]
    activity_map = {d.isoformat(): 0 for d in date_list}
    
    activity_query = db.query(
        cast(UploadedImage.uploaded_at, Date).label("upload_date"),
        func.count(UploadedImage.id)
    ).filter(
        UploadedImage.user_id == user_id,
        UploadedImage.uploaded_at >= datetime.combine(start_date, datetime.min.time())
    ).group_by("upload_date").all()
    
    for upload_date, count in activity_query:
        if isinstance(upload_date, datetime):
            upload_date = upload_date.date()
        date_str = upload_date.isoformat()
        if date_str in activity_map:
            activity_map[date_str] = count
            
    # Format activity response as list of dicts
    activity_chart = [
        {"date": d_str, "uploads": count}
        for d_str, count in sorted(activity_map.items())
    ]

    # 4. Top 10 detected objects
    top_objects_query = db.query(
        Detection.object_name,
        func.count(Detection.id).label("count")
    ).join(UploadedImage).filter(
        UploadedImage.user_id == user_id
    ).group_by(Detection.object_name).order_by(func.count(Detection.id).desc()).limit(10).all()
    
    top_objects = [
        {"name": obj_name, "count": count}
        for obj_name, count in top_objects_query
    ]
    
    return {
        "summary": {
            "total_images": total_images,
            "total_detections": total_detections,
            "most_detected_object": most_detected.capitalize() if most_detected else "None"
        },
        "confidence_distribution": confidence_bins,
        "upload_activity": activity_chart,
        "top_objects": top_objects
    }
