"""
Authentication dependencies for FastAPI endpoints.
Provides user authentication and authorization utilities.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_token
from app.db.session import SessionLocal
from app.models.user import User
from app.api.dependencies.database import get_db


# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        User object if authentication is successful
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
        
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current active user.
    Ensures the user account is not disabled.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object if user is active
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current superuser.
    Ensures the user has admin privileges.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object if user is a superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to optionally get the current user.
    Returns None if no valid token is provided.
    
    Args:
        token: JWT token from Authorization header (optional)
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    if not token:
        return None
        
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
            
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
        
    except JWTError:
        return None


def verify_device_auth(
    device_id: str,
    authorization: str,
    db: Session
):
    """
    Verify device authentication token for ESP32 sensors.
    
    Args:
        device_id: Sensor device identifier
        authorization: Authorization header value (Bearer token)
        db: Database session
        
    Returns:
        Sensor object if authentication is successful
        
    Raises:
        HTTPException: If token is invalid or sensor not found
    """
    from app.models.sensor import Sensor
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    
    # Find sensor and verify token
    sensor = db.query(Sensor).filter(
        Sensor.device_id == device_id,
        Sensor.auth_token == token
    ).first()
    
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return sensor
