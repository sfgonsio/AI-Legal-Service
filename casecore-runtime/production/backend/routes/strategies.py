"""
Strategy routes: GET strategies and details
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from models import Strategy, Weapon
from schemas import StrategyResponse, StrategyDetailResponse

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("/", response_model=List[StrategyResponse])
async def list_strategies(case_id: int = None, db: AsyncSession = Depends(get_db)):
    """List strategies, optionally filtered by case"""
    query = select(Strategy)
    if case_id:
        query = query.where(Strategy.case_id == case_id)
    result = await db.execute(query)
    strategies = result.scalars().all()
    return strategies


@router.get("/{strategy_id}", response_model=StrategyDetailResponse)
async def get_strategy(strategy_id: int, db: AsyncSession = Depends(get_db)):
    """Get strategy detail with associated weapons"""
    result = await db.execute(select(Strategy).where(Strategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")

    # Get associated weapons if weapons_json contains IDs
    weapons = []
    if strategy.weapons_json:
        weapon_ids = strategy.weapons_json.get("weapon_ids", [])
        if weapon_ids:
            weapons_result = await db.execute(
                select(Weapon).where(Weapon.id.in_(weapon_ids))
            )
            weapons = weapons_result.scalars().all()

    # Manually attach weapons to strategy for response
    strategy.weapons = weapons
    return strategy


@router.get("/case/{case_id}", response_model=List[StrategyResponse])
async def get_case_strategies(case_id: int, db: AsyncSession = Depends(get_db)):
    """Get all strategies for a case"""
    result = await db.execute(
        select(Strategy).where(Strategy.case_id == case_id)
    )
    strategies = result.scalars().all()
    return strategies
