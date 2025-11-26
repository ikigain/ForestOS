from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, Text, Index
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class Plant(BaseModel):
    __tablename__ = "plants_catalog"
    
    # Identification
    species_id = Column(String, unique=True, index=True, nullable=False)
    common_names = Column(JSON, nullable=False)  # List of common names
    scientific_name = Column(String, nullable=False, index=True)
    family = Column(String, nullable=True)
    
    # Care Requirements - Water
    water_frequency_days_min = Column(Integer, nullable=True)
    water_frequency_days_max = Column(Integer, nullable=True)
    soil_moisture_target_pct = Column(Integer, nullable=False, default=40)
    soil_moisture_min_pct = Column(Integer, nullable=False, default=25)
    drainage_required = Column(Boolean, default=True)
    
    # Care Requirements - Light
    light_level = Column(String, nullable=True)  # low, medium, bright_indirect, bright_direct
    min_lux = Column(Integer, nullable=True)
    optimal_lux_min = Column(Integer, nullable=True)
    optimal_lux_max = Column(Integer, nullable=True)
    
    # Care Requirements - Climate
    temp_celsius_min = Column(Integer, nullable=True)
    temp_celsius_optimal_min = Column(Integer, nullable=True)
    temp_celsius_optimal_max = Column(Integer, nullable=True)
    temp_celsius_max = Column(Integer, nullable=True)
    humidity_pct_min = Column(Integer, nullable=True)
    humidity_pct_optimal_min = Column(Integer, nullable=True)
    humidity_pct_optimal_max = Column(Integer, nullable=True)
    
    # Additional Info
    growth_rate = Column(String, nullable=True)  # slow, medium, fast
    toxicity_pets = Column(String, nullable=True)
    toxicity_humans = Column(String, nullable=True)
    health_indicators = Column(JSON, nullable=True)  # Dict of symptom: cause
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    
    # Relationships
    user_plants = relationship("UserPlant", back_populates="plant_species")


# Note: Cannot create standard B-tree index on JSON column (common_names)
# Index only on scientific_name for text search
Index('idx_plant_scientific_name_search', Plant.scientific_name)
