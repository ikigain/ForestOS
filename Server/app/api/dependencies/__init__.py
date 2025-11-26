"""
API dependencies package.
Exports commonly used dependencies for FastAPI endpoints.
"""
from app.api.dependencies.database import get_db
from app.api.dependencies.auth import (
    get_current_user,
    get_current_active_user,
    get_current_superuser,
    get_optional_current_user,
    oauth2_scheme
)

__all__ = [
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "get_current_superuser",
    "get_optional_current_user",
    "oauth2_scheme"
]
