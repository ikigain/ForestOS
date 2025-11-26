from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
from datetime import datetime


class SensorReading(BaseModel):
    __tablename__ = "sensor_readings"
    
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False, index=True)
    
    # Sensor values
    moisture_pct = Column(Float, nullable=False)
    temperature_celsius = Column(Float, nullable=True)
    humidity_pct = Column(Float, nullable=True)
    light_lux = Column(Integer, nullable=True)
    battery_voltage = Column(Float, nullable=True)
    
    # Timestamp (override default to allow ESP32 to send timestamp)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    sensor = relationship("Sensor", back_populates="readings")


# Optimize for time-series queries
Index('idx_sensor_readings_time', SensorReading.sensor_id, SensorReading.timestamp.desc())
