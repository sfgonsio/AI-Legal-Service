"""
Document routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from models import Document
from schemas import DocumentResponse, DocumentDetailResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(case_id: int = None, db: AsyncSession = Depends(get_db)):
    """List documents, optionally filtered by case"""
    query = select(Document)
    if case_id:
        query = query.where(Document.case_id == case_id)
    result = await db.execute(query)
    documents = result.scalars().all()
    return documents


@router.get("/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    """Get document detail with full text"""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.get("/case/{case_id}", response_model=List[DocumentResponse])
async def get_case_documents(case_id: int, db: AsyncSession = Depends(get_db)):
    """Get all documents for a case"""
    result = await db.execute(
        select(Document).where(Document.case_id == case_id)
    )
    documents = result.scalars().all()
    return documents
