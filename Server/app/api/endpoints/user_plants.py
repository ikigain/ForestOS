"""
User plants endpoints for managing individual plant instances.
"""
from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.models.user_plant import UserPlant
from app.models.plant import Plant
from app.schemas.user_plant import (
    UserPlantCreate,
    UserPlantUpdate,
    UserPlantResponse,
    UserPlantListResponse
)

router = APIRouter()


@router.post("/", response_model=UserPlantResponse, status_code=status.HTTP_201_CREATED)
def create_user_plant(
    plant_in: UserPlantCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new plant instance for the current user.
    
    Args:
        plant_in: Plant creation data
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Created plant instance
        
    Raises:
        HTTPException: If species_id not found in catalog
    """
    # Verify plant species exists in catalog
    plant_species = db.query(Plant).filter(
        Plant.species_id == plant_in.species_id
    ).first()
    
    if not plant_species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plant species '{plant_in.species_id}' not found in catalog"
        )
    
    # Create user plant
    user_plant = UserPlant(
        user_id=current_user.id,
        species_id=plant_in.species_id,
        nickname=plant_in.nickname,
        location=plant_in.location,
        pot_size=plant_in.pot_size,
        pot_material=plant_in.pot_material,
        custom_water_frequency_days=plant_in.custom_water_frequency_days,
        auto_water_enabled=plant_in.auto_water_enabled,
        last_watered=datetime.utcnow() if plant_in.last_watered is None else plant_in.last_watered
    )
    
    db.add(user_plant)
    db.commit()
    db.refresh(user_plant)
    
    return user_plant


@router.get("/", response_model=UserPlantListResponse)
def list_user_plants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all plants belonging to the current user.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        List of user's plants with pagination info
    """
    # Query user's plants
    query = db.query(UserPlant).filter(UserPlant.user_id == current_user.id)
    
    total = query.count()
    plants = query.offset(skip).limit(limit).all()
    
    return {
        "plants": plants,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{plant_id}", response_model=UserPlantResponse)
def get_user_plant(
    plant_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get details of a specific user plant.
    
    Args:
        plant_id: ID of the user plant
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Plant details
        
    Raises:
        HTTPException: If plant not found or doesn't belong to user
    """
    plant = db.query(UserPlant).filter(
        UserPlant.id == plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found or doesn't belong to you"
        )
    
    return plant


@router.put("/{plant_id}", response_model=UserPlantResponse)
def update_user_plant(
    plant_id: int,
    plant_in: UserPlantUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update a user plant's information.
    
    Args:
        plant_id: ID of the user plant
        plant_in: Update data
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Updated plant instance
        
    Raises:
        HTTPException: If plant not found or doesn't belong to user
    """
    plant = db.query(UserPlant).filter(
        UserPlant.id == plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found or doesn't belong to you"
        )
    
    # Update fields
    update_data = plant_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plant, field, value)
    
    db.commit()
    db.refresh(plant)
    
    return plant


@router.delete("/{plant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_plant(
    plant_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a user plant.
    
    Args:
        plant_id: ID of the user plant
        current_user: Currently authenticated user
        db: Database session
        
    Raises:
        HTTPException: If plant not found or doesn't belong to user
    """
    plant = db.query(UserPlant).filter(
        UserPlant.id == plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found or doesn't belong to you"
        )
    
    db.delete(plant)
    db.commit()


@router.post("/{plant_id}/water", response_model=UserPlantResponse)
def water_plant_manually(
    plant_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Manually mark a plant as watered (updates last_watered timestamp).
    
    Args:
        plant_id: ID of the user plant
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Updated plant instance
        
    Raises:
        HTTPException: If plant not found or doesn't belong to user
    """
    plant = db.query(UserPlant).filter(
        UserPlant.id == plant_id,
        UserPlant.user_id == current_user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found or doesn't belong to you"
        )
    
    # Update last watered timestamp
    plant.last_watered = datetime.utcnow()
    
    db.commit()
    db.refresh(plant)
    
    return plant
