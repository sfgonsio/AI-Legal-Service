"""
Weapon routes: GET, PATCH, simulate
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from models import Weapon, AttorneyEdit
from schemas import (
    WeaponResponse, WeaponDetailResponse, WeaponUpdate,
    SimulationRequest, SimulateResponse
)
from agents.opposition_agent import predict_defense_response

router = APIRouter(prefix="/weapons", tags=["weapons"])


@router.get("/", response_model=List[WeaponResponse])
async def list_weapons(case_id: int = None, db: AsyncSession = Depends(get_db)):
    """List all weapons, optionally filtered by case"""
    query = select(Weapon)
    if case_id:
        query = query.where(Weapon.case_id == case_id)
    result = await db.execute(query)
    weapons = result.scalars().all()
    return weapons


@router.get("/{weapon_id}", response_model=WeaponDetailResponse)
async def get_weapon(weapon_id: int, db: AsyncSession = Depends(get_db)):
    """Get weapon detail"""
    result = await db.execute(select(Weapon).where(Weapon.id == weapon_id))
    weapon = result.scalar_one_or_none()
    if not weapon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weapon not found")
    return weapon


@router.patch("/{weapon_id}", response_model=WeaponDetailResponse)
async def update_weapon(
    weapon_id: int,
    weapon_update: WeaponUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update weapon (attorney edits)"""
    result = await db.execute(select(Weapon).where(Weapon.id == weapon_id))
    db_weapon = result.scalar_one_or_none()
    if not db_weapon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weapon not found")

    # Track original values for audit trail
    update_data = weapon_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        original_value = getattr(db_weapon, field)
        if original_value != value:
            # Create audit entry
            edit = AttorneyEdit(
                weapon_id=weapon_id,
                field_name=field,
                original_value=str(original_value),
                edited_value=str(value),
                status="staged"
            )
            db.add(edit)
        setattr(db_weapon, field, value)

    await db.commit()
    await db.refresh(db_weapon)
    return db_weapon


@router.post("/{weapon_id}/simulate", response_model=SimulateResponse)
async def simulate_response(
    weapon_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Simulate opposition response to weapon"""
    result = await db.execute(select(Weapon).where(Weapon.id == weapon_id))
    weapon = result.scalar_one_or_none()
    if not weapon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weapon not found")

    # Get prediction from opposition agent
    response_dict = await predict_defense_response(weapon.__dict__)

    return SimulateResponse(**response_dict)


@router.post("/{weapon_id}/deploy", status_code=status.HTTP_200_OK)
async def deploy_weapon(weapon_id: int, db: AsyncSession = Depends(get_db)):
    """Deploy weapon (mark as deployed)"""
    result = await db.execute(select(Weapon).where(Weapon.id == weapon_id))
    weapon = result.scalar_one_or_none()
    if not weapon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weapon not found")

    weapon.status = "deployed"
    await db.commit()
    await db.refresh(weapon)
    return weapon
