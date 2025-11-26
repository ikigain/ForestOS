from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SensorReadingBase(BaseModel):
    sensor_id: int
    moisture_pct: float
    temperature_celsius: Optional[float] = None
    humidity_pct: Optional[float] = None
    light_lux: Optional[int] = None
    battery_voltage: Optional[float] = None
    timestamp: datetime


class SensorReadingCreate(SensorReadingBase):
    pass


class SensorReading(SensorReadingBase):
    id: int

    class Config:
        orm_mode = True


# Response schemas
ReadingResponse = SensorReading


class ReadingListResponse(BaseModel):
    readings: list[ReadingResponse]
    total: int
    skip: int
    limit: int
