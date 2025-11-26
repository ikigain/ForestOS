"""
Watering event schemas for API validation.
"""
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
from enum import Enum


class WateringTrigger(str, Enum):
    manual = "manual"
    automatic = "automatic"
    scheduled = "scheduled"


class WateringStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class WateringEventBase(BaseModel):
    plant_id: int
    trigger: WateringTrigger
    status: WateringStatus
    scheduled_time: datetime
    completed_time: Optional[datetime] = None
    water_ml: Optional[float] = None
    duration_seconds: Optional[int] = None
    moisture_before_pct: Optional[float] = None
    moisture_after_pct: Optional[float] = None
    notes: Optional[str] = None


class WateringEventCreate(BaseModel):
    plant_id: int
    trigger: WateringTrigger = WateringTrigger.manual
    water_ml: Optional[float] = None
    notes: Optional[str] = None


class WateringEventUpdate(BaseModel):
    status: Optional[WateringStatus] = None
    completed_time: Optional[datetime] = None
    water_ml: Optional[float] = None
    duration_seconds: Optional[int] = None
    moisture_before_pct: Optional[float] = None
    moisture_after_pct: Optional[float] = None
    notes: Optional[str] = None


class WateringEvent(WateringEventBase):
    id: int

    class Config:
        orm_mode = True


# Response schemas
WateringEventResponse = WateringEvent


class WateringEventListResponse(BaseModel):
    events: list[WateringEventResponse]
    total: int
    skip: int
    limit: int


class WateringStatistics(BaseModel):
    plant_id: int
    period_days: int
    total_events: int
    total_water_ml: float
    average_interval_days: Optional[float]
    trigger_counts: Dict[str, int]
    last_watered: Optional[str]  # ISO datetime string
