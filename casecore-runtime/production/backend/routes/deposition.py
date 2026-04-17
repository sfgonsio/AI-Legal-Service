"""
Deposition routes: WebSocket for real-time feed, session management
"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
from typing import List, Set

from database import get_db
from models import DepositionSession
from schemas import DepositionSessionCreate, DepositionSessionResponse, DepositionTranscriptUpdate
from agents.deposition_agent import (
    suggest_follow_up_questions,
    analyze_testimony,
    flag_perjury_opportunity
)

router = APIRouter(prefix="/deposition", tags=["deposition"])

# WebSocket connection manager for real-time deposition feed
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@router.post("/sessions", response_model=DepositionSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_deposition_session(
    session_data: DepositionSessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new deposition session"""
    db_session = DepositionSession(**session_data.dict())
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session


@router.get("/sessions/{session_id}", response_model=DepositionSessionResponse)
async def get_deposition_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get deposition session"""
    result = await db.execute(
        select(DepositionSession).where(DepositionSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.get("/sessions/case/{case_id}", response_model=List[DepositionSessionResponse])
async def get_case_sessions(
    case_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all deposition sessions for case"""
    result = await db.execute(
        select(DepositionSession).where(DepositionSession.case_id == case_id)
    )
    sessions = result.scalars().all()
    return sessions


@router.patch("/sessions/{session_id}/transcript", response_model=DepositionSessionResponse)
async def update_transcript(
    session_id: int,
    transcript_update: DepositionTranscriptUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update deposition transcript"""
    result = await db.execute(
        select(DepositionSession).where(DepositionSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    session.transcript_text = transcript_update.transcript_text
    await db.commit()
    await db.refresh(session)
    return session


@router.patch("/sessions/{session_id}/close", response_model=DepositionSessionResponse)
async def close_deposition_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Close deposition session"""
    result = await db.execute(
        select(DepositionSession).where(DepositionSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    session.status = "closed"
    await db.commit()
    await db.refresh(session)
    return session


@router.websocket("/ws/{session_id}")
async def websocket_deposition(websocket: WebSocket, session_id: int):
    """
    WebSocket endpoint for real-time deposition assistant
    Receives: {type: 'testimony', text: 'witness testimony...'}
    Sends: {type: 'suggestion', questions: [...], analysis: {...}}
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "testimony":
                testimony = data.get("text", "")

                # Analyze testimony for issues
                analysis = await analyze_testimony(
                    testimony,
                    evidence=[],  # Would be populated from database
                    weapons=[]    # Would be populated from database
                )

                # Suggest follow-up questions
                follow_ups = await suggest_follow_up_questions(
                    witness_name=data.get("witness_name", "Unknown"),
                    prior_answer=testimony,
                    available_weapons=[],
                    deposition_context={}
                )

                # Check for perjury opportunity
                perjury_flag = await flag_perjury_opportunity(
                    testimony,
                    prior_deposition=None,
                    documents=[],
                    weapons=[]
                )

                # Broadcast suggestions to all connected clients
                response = {
                    "type": "suggestion",
                    "session_id": session_id,
                    "analysis": analysis,
                    "follow_up_questions": follow_ups,
                    "perjury_flag": perjury_flag
                }
                await manager.broadcast(response)

            elif message_type == "close":
                break

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        raise
