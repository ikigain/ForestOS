"""
API endpoints package.
"""
from app.api.endpoints import auth, plants, user_plants, sensors, watering, alerts

__all__ = ["auth", "plants", "user_plants", "sensors", "watering", "alerts"]
