from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
import enum


class PotMaterial(str, enum.Enum):
    TERRACOTTA = "terracotta"
    PLASTIC = "plastic"
    CERAMIC_GLAZED = "ceramic_glazed"
    FABRIC = "fabric"
    OTHER = "other"


class PotSize(str, enum.Enum):
    SMALL = "small"      # < 1L
    MEDIUM = "medium"    # 1-5L
    LARGE = "large"      # 5-10L
    XLARGE = "xlarge"    # > 10L


class UserPlant(BaseModel):
    __tablename__ = "user_plants"
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Plant species relationship
    species_id = Column(String, ForeignKey("plants_catalog.species_id"), nullable=False)
    
    # User-specific info
    nickname = Column(String, nullable=False)
    location = Column(String, nullable=True)  # "living room", "bedroom", etc.
    pot_size = Column(SQLEnum(PotSize), nullable=True, default=PotSize.MEDIUM)
    pot_material = Column(SQLEnum(PotMaterial), nullable=True, default=PotMaterial.PLASTIC)
    notes = Column(String, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_watered = Column(DateTime, nullable=True)
    
    # Custom thresholds (override species defaults)
    custom_moisture_target = Column(Integer, nullable=True)
    custom_moisture_min = Column(Integer, nullable=True)
    auto_watering_enabled = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="user_plants")
    plant_species = relationship("Plant", back_populates="user_plants")
    sensors = relationship("Sensor", back_populates="user_plant", cascade="all, delete-orphan")
    watering_events = relationship("WateringEvent", back_populates="user_plant", cascade="all, delete-orphan")
