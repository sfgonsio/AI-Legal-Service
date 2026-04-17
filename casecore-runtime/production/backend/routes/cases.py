"""
Case CRUD routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from models import Case
from schemas import CaseCreate, CaseUpdate, CaseResponse, CaseDetailResponse

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(case: CaseCreate, db: AsyncSession = Depends(get_db)):
    """Create a new case"""
    db_case = Case(**case.dict())
    db.add(db_case)
    await db.commit()
    await db.refresh(db_case)
    return db_case


@router.get("/", response_model=List[CaseResponse])
async def list_cases(db: AsyncSession = Depends(get_db)):
    """List all cases"""
    result = await db.execute(select(Case))
    cases = result.scalars().all()
    return cases


@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case(case_id: int, db: AsyncSession = Depends(get_db)):
    """Get case detail with all related data"""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case


@router.patch("/{case_id}", response_model=CaseResponse)
async def update_case(case_id: int, case_update: CaseUpdate, db: AsyncSession = Depends(get_db)):
    """Update case"""
    result = await db.execute(select(Case).where(Case.id == case_id))
    db_case = result.scalar_one_or_none()
    if not db_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    update_data = case_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_case, field, value)

    await db.commit()
    await db.refresh(db_case)
    return db_case


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(case_id: int, db: AsyncSession = Depends(get_db)):
    """Delete case and all related data"""
    result = await db.execute(select(Case).where(Case.id == case_id))
    db_case = result.scalar_one_or_none()
    if not db_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    await db.delete(db_case)
    await db.commit()
    return None
