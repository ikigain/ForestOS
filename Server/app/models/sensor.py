from sqlalchemy import Column, String, Integer, ForeignKey, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class Sensor(BaseModel):
    __tablename__ = "sensors"
    
    # Device identification
    device_id = Column(String, unique=True, index=True, nullable=False)
    hardware_version = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    
    # Authentication
    auth_token = Column(String, unique=True, nullable=False)
    
    # Assignment
    user_plant_id = Column(Integer, ForeignKey("user_plants.id"), nullable=True, index=True)
    
    # Status
    is_online = Column(Boolean, default=False)
    battery_level = Column(Float, nullable=True)  # Percentage
    last_seen = Column(DateTime, nullable=True)
    
    # Calibration
    moisture_dry_value = Column(Integer, nullable=True)   # Raw ADC value in air
    moisture_wet_value = Column(Integer, nullable=True)   # Raw ADC value in water
    
    # Relationships
    user_plant = relationship("UserPlant", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor", cascade="all, delete-orphan")
