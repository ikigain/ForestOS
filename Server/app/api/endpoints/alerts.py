"""
Alert endpoints for managing user notifications.
"""
from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.models.user_plant import UserPlant
from app.models.alert import Alert, AlertType
from app.schemas.alert import (
    AlertCreate,
    AlertResponse,
    AlertListResponse
)

router = APIRouter()


@router.get("/", response_model=AlertListResponse)
def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    is_read: bool = Query(None, description="Filter by read status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all alerts for the current user.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_read: Optional filter for read/unread alerts
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        List of alerts with pagination
    """
    # Get user's plant IDs
    plant_ids = db.query(UserPlant.id).filter(
        UserPlant.user_id == current_user.id
    ).all()
    plant_ids = [p[0] for p in plant_ids]
    
    # Build query
    query = db.query(Alert).filter(Alert.plant_id.in_(plant_ids))
    
    # Apply read filter if specified
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)
    
    # Order by timestamp descending (newest first)
    query = query.order_by(Alert.timestamp.desc())
    
    total = query.count()
    alerts = query.offset(skip).limit(limit).all()
    
    return {
        "alerts": alerts,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get details of a specific alert.
    
    Args:
        alert_id: ID of the alert
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Alert details
        
    Raises:
        HTTPException: If alert not found or doesn't belong to user's plants
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Verify plant belongs to user
    plant = db.query(UserPlant).filter(
        UserPlant.id == alert.plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Alert doesn't belong to your plants"
        )
    
    return alert


@router.post("/{alert_id}/mark-read", response_model=AlertResponse)
def mark_alert_read(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Mark an alert as read.
    
    Args:
        alert_id: ID of the alert
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Updated alert
        
    Raises:
        HTTPException: If alert not found or doesn't belong to user
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Verify ownership
    plant = db.query(UserPlant).filter(
        UserPlant.id == alert.plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Alert doesn't belong to your plants"
        )
    
    # Mark as read
    alert.is_read = True
    
    db.commit()
    db.refresh(alert)
    
    return alert


@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
def mark_all_alerts_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Mark all unread alerts as read for the current user.
    
    Args:
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Count of alerts marked as read
    """
    # Get user's plant IDs
    plant_ids = db.query(UserPlant.id).filter(
        UserPlant.user_id == current_user.id
    ).all()
    plant_ids = [p[0] for p in plant_ids]
    
    # Update all unread alerts
    updated_count = db.query(Alert).filter(
        Alert.plant_id.in_(plant_ids),
        Alert.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return {
        "message": f"Marked {updated_count} alerts as read",
        "count": updated_count
    }


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete an alert.
    
    Args:
        alert_id: ID of the alert
        current_user: Currently authenticated user
        db: Database session
        
    Raises:
        HTTPException: If alert not found or doesn't belong to user
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Verify ownership
    plant = db.query(UserPlant).filter(
        UserPlant.id == alert.plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Alert doesn't belong to your plants"
        )
    
    db.delete(alert)
    db.commit()
