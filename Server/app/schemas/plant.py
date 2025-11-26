from pydantic import BaseModel
from typing import List, Optional


class PlantBase(BaseModel):
    species_id: str
    common_names: List[str]
    scientific_name: str
    family: Optional[str] = None
    water_frequency_days_min: Optional[int]
    water_frequency_days_max: Optional[int]
    soil_moisture_target_pct: int
    soil_moisture_min_pct: int
    drainage_required: bool
    light_level: Optional[str]
    min_lux: Optional[int]
    optimal_lux_min: Optional[int]
    optimal_lux_max: Optional[int]
    temp_celsius_min: Optional[int]
    temp_celsius_optimal_min: Optional[int]
    temp_celsius_optimal_max: Optional[int]
    temp_celsius_max: Optional[int]
    humidity_pct_min: Optional[int]
    humidity_pct_optimal_min: Optional[int]
    humidity_pct_optimal_max: Optional[int]
    growth_rate: Optional[str]
    toxicity_pets: Optional[str]
    toxicity_humans: Optional[str]
    health_indicators: Optional[dict]
    description: Optional[str]
    image_url: Optional[str]


class PlantCreate(PlantBase):
    pass


class PlantUpdate(BaseModel):
    description: Optional[str] = None


class Plant(PlantBase):
    id: int

    class Config:
        orm_mode = True


# Response schemas
PlantResponse = Plant


class PlantListResponse(BaseModel):
    plants: List[PlantResponse]
    total: int
    skip: int
    limit: int
