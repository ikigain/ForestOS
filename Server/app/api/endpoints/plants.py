"""
Plant catalog endpoints for browsing and searching plant species.
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.plant import Plant
from app.schemas.plant import PlantResponse, PlantListResponse

router = APIRouter()


@router.get("/", response_model=PlantListResponse)
def list_plants(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    light_level: Optional[str] = Query(None, description="Filter by light level (low, medium, bright_indirect, bright_direct)"),
    growth_rate: Optional[str] = Query(None, description="Filter by growth rate (slow, medium, fast)"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get list of plants from catalog with optional filters.
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        light_level: Optional filter by light requirements
        growth_rate: Optional filter by growth rate
        db: Database session
        
    Returns:
        List of plants and total count
    """
    # Build query
    query = db.query(Plant)
    
    # Apply filters
    if light_level:
        query = query.filter(Plant.light_level == light_level)
    if growth_rate:
        query = query.filter(Plant.growth_rate == growth_rate)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    plants = query.offset(skip).limit(limit).all()
    
    return {
        "plants": plants,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/search", response_model=List[PlantResponse])
def search_plants(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Search plants by name (common names or scientific name).
    
    Args:
        q: Search query string
        limit: Maximum number of results
        db: Database session
        
    Returns:
        List of matching plants
    """
    # Search in scientific name (case-insensitive)
    query_lower = q.lower()
    plants = db.query(Plant).filter(
        Plant.scientific_name.ilike(f"%{query_lower}%")
    ).limit(limit).all()
    
    # TODO: Also search in JSON common_names field
    # This requires using PostgreSQL JSON operators
    # For now, just search scientific name
    
    return plants


@router.get("/{species_id}", response_model=PlantResponse)
def get_plant(
    species_id: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get detailed information about a specific plant species.
    
    Args:
        species_id: Unique species identifier
        db: Database session
        
    Returns:
        Plant details
        
    Raises:
        HTTPException: If plant not found
    """
    plant = db.query(Plant).filter(Plant.species_id == species_id).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plant with species_id '{species_id}' not found"
        )
    
    return plant


@router.get("/by-care-level/{care_level}", response_model=List[PlantResponse])
def get_plants_by_care_level(
    care_level: str = Query(..., regex="^(easy|moderate|difficult)$"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get plants filtered by care difficulty level.
    Easy: low light, infrequent watering
    Moderate: medium requirements
    Difficult: specific requirements
    
    Args:
        care_level: Difficulty level (easy, moderate, difficult)
        limit: Maximum number of results
        db: Database session
        
    Returns:
        List of plants matching care level
    """
    query = db.query(Plant)
    
    if care_level == "easy":
        # Low light, infrequent watering (high max frequency days)
        query = query.filter(
            Plant.light_level == "low",
            Plant.water_frequency_days_max >= 10
        )
    elif care_level == "moderate":
        # Medium light, moderate watering
        query = query.filter(
            Plant.light_level.in_(["medium", "bright_indirect"]),
            Plant.water_frequency_days_max.between(5, 10)
        )
    else:  # difficult
        # Specific light needs or frequent watering
        query = query.filter(
            (Plant.light_level == "bright_direct") |
            (Plant.water_frequency_days_max < 5)
        )
    
    plants = query.limit(limit).all()
    return plants
