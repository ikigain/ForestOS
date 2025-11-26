from pydantic import BaseModel
from typing import Optional
from enum import Enum


class PotMaterial(str, Enum):
    terracotta = "terracotta"
    plastic = "plastic"
    ceramic_glazed = "ceramic_glazed"
    fabric = "fabric"
    other = "other"


class PotSize(str, Enum):
    small = "small"
    medium = "medium"
    large = "large"
    xlarge = "xlarge"


class UserPlantBase(BaseModel):
    species_id: str
    nickname: str
    location: Optional[str] = None
    pot_size: Optional[PotSize] = PotSize.medium
    pot_material: Optional[PotMaterial] = PotMaterial.plastic
    notes: Optional[str] = None
    is_active: Optional[bool] = True
    last_watered: Optional[str] = None  # ISO datetime string
    custom_moisture_target: Optional[int] = None
    custom_moisture_min: Optional[int] = None
    auto_watering_enabled: Optional[bool] = True


class UserPlantCreate(UserPlantBase):
    pass


class UserPlantUpdate(BaseModel):
    nickname: Optional[str] = None
    location: Optional[str] = None
    pot_size: Optional[PotSize] = None
    pot_material: Optional[PotMaterial] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    last_watered: Optional[str] = None
    custom_moisture_target: Optional[int] = None
    custom_moisture_min: Optional[int] = None
    auto_watering_enabled: Optional[bool] = None


class UserPlant(UserPlantBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


# Response schemas
UserPlantResponse = UserPlant


class UserPlantListResponse(BaseModel):
    plants: list[UserPlantResponse]
    total: int
    skip: int
    limit: int
