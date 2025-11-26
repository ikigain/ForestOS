"""
Sensor device endpoints for hardware integration.
"""
from typing import Any, List
from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.api.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.models.user_plant import UserPlant
from app.models.sensor import Sensor
from app.models.reading import SensorReading
from app.schemas.sensor import (
    SensorCreate,
    SensorUpdate,
    SensorResponse,
    SensorListResponse,
    SensorReadingSubmit
)
from app.schemas.reading import ReadingResponse, ReadingListResponse

router = APIRouter()


@router.post("/", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def register_sensor(
    sensor_in: SensorCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new sensor device and pair it with a user plant.
    
    Args:
        sensor_in: Sensor registration data (device_id, plant_id)
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Created sensor object
        
    Raises:
        HTTPException: If device_id already exists or plant not found/not owned
    """
    # Check if device already registered
    existing_sensor = db.query(Sensor).filter(
        Sensor.device_id == sensor_in.device_id
    ).first()
    
    if existing_sensor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sensor with device_id '{sensor_in.device_id}' already registered"
        )
    
    # Verify plant exists and belongs to user
    plant = db.query(UserPlant).filter(
        UserPlant.id == sensor_in.plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found or doesn't belong to you"
        )
    
    # Create sensor with auth token
    sensor = Sensor(
        device_id=sensor_in.device_id,
        plant_id=sensor_in.plant_id,
        auth_token=secrets.token_urlsafe(32),  # Generate secure token for device auth
        battery_level=100,  # Initial assumption
        is_online=True,
        last_seen=datetime.utcnow()
    )
    
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    
    return sensor


@router.get("/", response_model=SensorListResponse)
def list_sensors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all sensors belonging to current user's plants.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        List of sensors with pagination info
    """
    # Get user's plant IDs
    plant_ids = db.query(UserPlant.id).filter(
        UserPlant.user_id == current_user.id
    ).all()
    plant_ids = [p[0] for p in plant_ids]
    
    # Query sensors for these plants
    query = db.query(Sensor).filter(Sensor.plant_id.in_(plant_ids))
    
    total = query.count()
    sensors = query.offset(skip).limit(limit).all()
    
    return {
        "sensors": sensors,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{device_id}", response_model=SensorResponse)
def get_sensor(
    device_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get details of a specific sensor.
    
    Args:
        device_id: Sensor device identifier
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Sensor details
        
    Raises:
        HTTPException: If sensor not found or doesn't belong to user's plants
    """
    sensor = db.query(Sensor).filter(Sensor.device_id == device_id).first()
    
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found"
        )
    
    # Verify plant belongs to user
    plant = db.query(UserPlant).filter(
        UserPlant.id == sensor.plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sensor doesn't belong to your plants"
        )
    
    return sensor


@router.put("/{device_id}", response_model=SensorResponse)
def update_sensor(
    device_id: str,
    sensor_in: SensorUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update sensor information (battery level, calibration, etc.).
    
    Args:
        device_id: Sensor device identifier
        sensor_in: Update data
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Updated sensor
        
    Raises:
        HTTPException: If sensor not found or doesn't belong to user
    """
    sensor = db.query(Sensor).filter(Sensor.device_id == device_id).first()
    
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found"
        )
    
    # Verify ownership
    plant = db.query(UserPlant).filter(
        UserPlant.id == sensor.plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sensor doesn't belong to your plants"
        )
    
    # Update fields
    update_data = sensor_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sensor, field, value)
    
    # Update last_seen if online status changed
    if "is_online" in update_data:
        sensor.last_seen = datetime.utcnow()
    
    db.commit()
    db.refresh(sensor)
    
    return sensor


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor(
    device_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Unpair and delete a sensor device.
    
    Args:
        device_id: Sensor device identifier
        current_user: Currently authenticated user
        db: Database session
        
    Raises:
        HTTPException: If sensor not found or doesn't belong to user
    """
    sensor = db.query(Sensor).filter(Sensor.device_id == device_id).first()
    
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found"
        )
    
    # Verify ownership
    plant = db.query(UserPlant).filter(
        UserPlant.id == sensor.plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sensor doesn't belong to your plants"
        )
    
    db.delete(sensor)
    db.commit()


@router.post("/{device_id}/readings", response_model=ReadingResponse, status_code=status.HTTP_201_CREATED)
def submit_reading(
    device_id: str,
    reading_in: SensorReadingSubmit,
    authorization: str = Header(..., description="Device authentication token"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Submit a new sensor reading (used by ESP32 devices).
    Requires device authentication via Bearer token.
    
    Args:
        device_id: Sensor device identifier
        reading_in: Reading data (moisture, temp, humidity, light)
        authorization: Authorization header with Bearer token
        db: Database session
        
    Returns:
        Created reading object
        
    Raises:
        HTTPException: If sensor not found or authentication fails
    """
    from app.api.dependencies.auth import verify_device_auth
    
    # Verify device authentication
    sensor = verify_device_auth(device_id, authorization, db)
    
    # Create reading
    reading = SensorReading(
        sensor_id=sensor.id,
        moisture_percent=reading_in.moisture_percent,
        temperature_celsius=reading_in.temperature_celsius,
        humidity_percent=reading_in.humidity_percent,
        light_lux=reading_in.light_lux,
        timestamp=datetime.utcnow()
    )
    
    db.add(reading)
    
    # Update sensor status
    sensor.is_online = True
    sensor.last_seen = datetime.utcnow()
    if reading_in.battery_level is not None:
        sensor.battery_level = reading_in.battery_level
    
    db.commit()
    db.refresh(reading)
    
    return reading


@router.get("/{device_id}/readings", response_model=ReadingListResponse)
def get_sensor_readings(
    device_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    hours: Optional[int] = Query(None, ge=1, le=168, description="Filter readings from last N hours"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get historical readings for a sensor.
    
    Args:
        device_id: Sensor device identifier
        skip: Number of records to skip
        limit: Maximum number of records (max 1000 for time-series data)
        hours: Optional filter for last N hours (max 7 days)
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        List of readings with pagination
        
    Raises:
        HTTPException: If sensor not found or doesn't belong to user
    """
    # Find sensor
    sensor = db.query(Sensor).filter(Sensor.device_id == device_id).first()
    
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found"
        )
    
    # Verify ownership
    plant = db.query(UserPlant).filter(
        UserPlant.id == sensor.plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sensor doesn't belong to your plants"
        )
    
    # Build query
    query = db.query(SensorReading).filter(SensorReading.sensor_id == sensor.id)
    
    # Apply time filter if specified
    if hours:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(SensorReading.timestamp >= time_threshold)
    
    # Order by timestamp descending (newest first)
    query = query.order_by(SensorReading.timestamp.desc())
    
    total = query.count()
    readings = query.offset(skip).limit(limit).all()
    
    return {
        "readings": readings,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{device_id}/readings/latest", response_model=ReadingResponse)
def get_latest_reading(
    device_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get the most recent reading for a sensor.
    
    Args:
        device_id: Sensor device identifier
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Latest reading
        
    Raises:
        HTTPException: If sensor not found, no readings, or doesn't belong to user
    """
    # Find sensor
    sensor = db.query(Sensor).filter(Sensor.device_id == device_id).first()
    
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found"
        )
    
    # Verify ownership
    plant = db.query(UserPlant).filter(
        UserPlant.id == sensor.plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sensor doesn't belong to your plants"
        )
    
    # Get latest reading
    reading = db.query(SensorReading).filter(
        SensorReading.sensor_id == sensor.id
    ).order_by(SensorReading.timestamp.desc()).first()
    
    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No readings found for this sensor"
        )
    
    return reading
