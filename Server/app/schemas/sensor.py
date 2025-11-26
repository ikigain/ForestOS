from pydantic import BaseModel
from typing import Optional


class SensorBase(BaseModel):
    device_id: str
    hardware_version: Optional[str] = None
    firmware_version: Optional[str] = None
    auth_token: str
    user_plant_id: Optional[int] = None
    is_online: Optional[bool] = False
    battery_level: Optional[float] = None
    last_seen: Optional[str] = None  # ISO datetime string
    moisture_dry_value: Optional[int] = None
    moisture_wet_value: Optional[int] = None


class SensorCreate(SensorBase):
    pass


class SensorUpdate(BaseModel):
    is_online: Optional[bool] = None
    battery_level: Optional[float] = None
    last_seen: Optional[str] = None


class Sensor(SensorBase):
    id: int
    auth_token: str  # Expose auth token in response for device registration

    class Config:
        orm_mode = True


# Response schemas
SensorResponse = Sensor


class SensorListResponse(BaseModel):
    sensors: list[SensorResponse]
    total: int
    skip: int
    limit: int


# Schema for sensor reading submission (from ESP32 devices)
class SensorReadingSubmit(BaseModel):
    moisture_percent: float
    temperature_celsius: Optional[float] = None
    humidity_percent: Optional[float] = None
    light_lux: Optional[int] = None
    battery_level: Optional[float] = None
