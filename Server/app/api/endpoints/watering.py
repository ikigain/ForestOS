"""
Watering endpoints for irrigation control and history.
"""
from typing import Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.models.user_plant import UserPlant
from app.models.watering import WateringEvent, WateringTrigger, WateringStatus
from app.schemas.watering import (
    WateringEventCreate,
    WateringEventResponse,
    WateringEventListResponse,
    WateringStatistics
)

router = APIRouter()


@router.post("/{plant_id}/trigger", response_model=WateringEventResponse, status_code=status.HTTP_201_CREATED)
def trigger_watering(
    plant_id: int,
    trigger: WateringTrigger = WateringTrigger.manual,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Trigger a watering event for a specific plant.
    
    Args:
        plant_id: ID of the user plant
        trigger: Watering trigger type (manual, automatic, scheduled)
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Created watering event
        
    Raises:
        HTTPException: If plant not found or doesn't belong to user
    """
    # Verify plant exists and belongs to user
    plant = db.query(UserPlant).filter(
        UserPlant.id == plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found or doesn't belong to you"
        )
    
    # Create watering event
    watering_event = WateringEvent(
        plant_id=plant_id,
        trigger=trigger,
        status=WateringStatus.pending,
        scheduled_time=datetime.utcnow()
    )
    
    db.add(watering_event)
    
    # Update plant's last_watered timestamp
    plant.last_watered = datetime.utcnow()
    
    db.commit()
    db.refresh(watering_event)
    
    return watering_event


@router.get("/{plant_id}/history", response_model=WateringEventListResponse)
def get_watering_history(
    plant_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    days: int = Query(30, ge=1, le=365, description="Number of days of history to retrieve"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get watering history for a specific plant.
    
    Args:
        plant_id: ID of the user plant
        skip: Number of records to skip
        limit: Maximum number of records to return
        days: Number of days of history (default 30)
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        List of watering events with pagination
        
    Raises:
        HTTPException: If plant not found or doesn't belong to user
    """
    # Verify plant ownership
    plant = db.query(UserPlant).filter(
        UserPlant.id == plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found or doesn't belong to you"
        )
    
    # Build query
    time_threshold = datetime.utcnow() - timedelta(days=days)
    query = db.query(WateringEvent).filter(
        WateringEvent.plant_id == plant_id,
        WateringEvent.scheduled_time >= time_threshold
    ).order_by(WateringEvent.scheduled_time.desc())
    
    total = query.count()
    events = query.offset(skip).limit(limit).all()
    
    return {
        "events": events,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{plant_id}/statistics", response_model=WateringStatistics)
def get_watering_statistics(
    plant_id: int,
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get watering statistics for a plant over specified period.
    
    Args:
        plant_id: ID of the user plant
        days: Number of days to analyze (default 30)
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Watering statistics
        
    Raises:
        HTTPException: If plant not found or doesn't belong to user
    """
    # Verify plant ownership
    plant = db.query(UserPlant).filter(
        UserPlant.id == plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found or doesn't belong to you"
        )
    
    # Calculate statistics
    time_threshold = datetime.utcnow() - timedelta(days=days)
    
    # Total watering events
    total_events = db.query(func.count(WateringEvent.id)).filter(
        WateringEvent.plant_id == plant_id,
        WateringEvent.scheduled_time >= time_threshold,
        WateringEvent.status == WateringStatus.completed
    ).scalar()
    
    # Total water volume (if recorded)
    total_volume = db.query(func.sum(WateringEvent.water_ml)).filter(
        WateringEvent.plant_id == plant_id,
        WateringEvent.scheduled_time >= time_threshold,
        WateringEvent.status == WateringStatus.completed,
        WateringEvent.water_ml.isnot(None)
    ).scalar() or 0
    
    # Average interval between waterings
    avg_interval = None
    if total_events > 1:
        events = db.query(WateringEvent.scheduled_time).filter(
            WateringEvent.plant_id == plant_id,
            WateringEvent.scheduled_time >= time_threshold,
            WateringEvent.status == WateringStatus.completed
        ).order_by(WateringEvent.scheduled_time.asc()).all()
        
        if len(events) > 1:
            intervals = []
            for i in range(1, len(events)):
                delta = (events[i][0] - events[i-1][0]).days
                intervals.append(delta)
            avg_interval = sum(intervals) / len(intervals) if intervals else None
    
    # Count by trigger type
    trigger_counts = {}
    for trigger in WateringTrigger:
        count = db.query(func.count(WateringEvent.id)).filter(
            WateringEvent.plant_id == plant_id,
            WateringEvent.scheduled_time >= time_threshold,
            WateringEvent.trigger == trigger,
            WateringEvent.status == WateringStatus.completed
        ).scalar()
        trigger_counts[trigger.value] = count
    
    return {
        "plant_id": plant_id,
        "period_days": days,
        "total_events": total_events,
        "total_water_ml": total_volume,
        "average_interval_days": avg_interval,
        "trigger_counts": trigger_counts,
        "last_watered": plant.last_watered.isoformat() if plant.last_watered else None
    }


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watering_event(
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a watering event (admin/correction purposes).
    
    Args:
        event_id: ID of the watering event
        current_user: Currently authenticated user
        db: Database session
        
    Raises:
        HTTPException: If event not found or doesn't belong to user's plant
    """
    # Find event
    event = db.query(WateringEvent).filter(WateringEvent.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watering event not found"
        )
    
    # Verify ownership through plant
    plant = db.query(UserPlant).filter(
        UserPlant.id == event.plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Watering event doesn't belong to your plants"
        )
    
    db.delete(event)
    db.commit()
