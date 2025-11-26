from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Relationships
    user_plants = relationship("UserPlant", back_populates="user", cascade="all, delete-orphan")
