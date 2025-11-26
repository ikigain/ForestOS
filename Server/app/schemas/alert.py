"""
Alert schemas for API validation.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class AlertType(str, Enum):
    low_moisture = "low_moisture"
    high_moisture = "high_moisture"
    low_temperature = "low_temperature"
    high_temperature = "high_temperature"
    low_light = "low_light"
    high_light = "high_light"
    sensor_offline = "sensor_offline"
    low_battery = "low_battery"
    watering_failed = "watering_failed"
    general = "general"


class AlertBase(BaseModel):
    plant_id: int
    alert_type: AlertType
    message: str
    is_read: bool = False
    timestamp: datetime


class AlertCreate(BaseModel):
    plant_id: int
    alert_type: AlertType
    message: str


class AlertUpdate(BaseModel):
    is_read: Optional[bool] = None


class Alert(AlertBase):
    id: int

    class Config:
        orm_mode = True


# Response schemas
AlertResponse = Alert


class AlertListResponse(BaseModel):
    alerts: list[AlertResponse]
    total: int
    skip: int
    limit: int
