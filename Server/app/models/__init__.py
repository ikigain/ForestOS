# Import all models here for Alembic to detect them
from app.models.user import User
from app.models.plant import Plant
from app.models.user_plant import UserPlant, PotMaterial, PotSize
from app.models.sensor import Sensor
from app.models.reading import SensorReading
from app.models.watering import WateringEvent, WateringTrigger, WateringStatus
from app.models.alert import Alert, AlertType

__all__ = [
    "User",
    "Plant",
    "UserPlant",
    "PotMaterial",
    "PotSize",
    "Sensor",
    "SensorReading",
    "WateringEvent",
    "WateringTrigger",
    "WateringStatus",
    "Alert",
    "AlertType",
]
