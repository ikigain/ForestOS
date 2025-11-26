from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Enum as SQLEnum, JSON
from app.db.base import BaseModel
import enum


class AlertType(str, enum.Enum):
    LOW_MOISTURE = "low_moisture"
    HIGH_MOISTURE = "high_moisture"
    SENSOR_OFFLINE = "sensor_offline"
    LOW_BATTERY = "low_battery"
    ANOMALY = "anomaly"
    WATERING_FAILED = "watering_failed"


class Alert(BaseModel):
    __tablename__ = "alerts"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_plant_id = Column(Integer, ForeignKey("user_plants.id"), nullable=True)
    
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    # Additional data
    data = Column(JSON, nullable=True)
