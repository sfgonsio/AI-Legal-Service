"""
Cause of Action routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from models import COA
from schemas import COAResponse, COADetailResponse

router = APIRouter(prefix="/coas", tags=["coas"])


@router.get("/", response_model=List[COAResponse])
async def list_coas(case_id: int = None, db: AsyncSession = Depends(get_db)):
    """List COAs, optionally filtered by case"""
    query = select(COA)
    if case_id:
        query = query.where(COA.case_id == case_id)
    result = await db.execute(query)
    coas = result.scalars().all()
    return coas


@router.get("/{coa_id}", response_model=COADetailResponse)
async def get_coa(coa_id: int, db: AsyncSession = Depends(get_db)):
    """Get COA detail with burden elements"""
    result = await db.execute(select(COA).where(COA.id == coa_id))
    coa = result.scalar_one_or_none()
    if not coa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="COA not found")
    return coa


@router.get("/case/{case_id}", response_model=List[COAResponse])
async def get_case_coas(case_id: int, db: AsyncSession = Depends(get_db)):
    """Get all COAs for a case"""
    result = await db.execute(
        select(COA).where(COA.case_id == case_id)
    )
    coas = result.scalars().all()
    return coas
