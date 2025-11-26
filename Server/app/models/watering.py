from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
from datetime import datetime
import enum


class WateringTrigger(str, enum.Enum):
    MANUAL = "manual"           # User pressed button in app
    AUTOMATIC = "automatic"     # System decided
    SCHEDULED = "scheduled"     # Time-based schedule


class WateringStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class WateringEvent(BaseModel):
    __tablename__ = "watering_events"
    
    user_plant_id = Column(Integer, ForeignKey("user_plants.id"), nullable=False, index=True)
    
    # Event details
    trigger = Column(SQLEnum(WateringTrigger), nullable=False)
    status = Column(SQLEnum(WateringStatus), default=WateringStatus.PENDING, nullable=False)
    
    # Measurements
    moisture_before = Column(Float, nullable=True)
    moisture_after = Column(Float, nullable=True)
    duration_ms = Column(Integer, nullable=True)  # Pump duration in milliseconds
    volume_ml = Column(Integer, nullable=True)    # Estimated volume
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = Column(String, nullable=True)
    
    # Relationships
    user_plant = relationship("UserPlant", back_populates="watering_events")
