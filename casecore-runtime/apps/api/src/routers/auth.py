"""
Authentication & Role Router

Routes users to the correct interface based on role:
  - CLIENT: intake narrative flow (limited view)
  - ATTORNEY: full dashboard (COA, burden, evidence, gaps)
  - ADMIN: system management (future)

For sandbox: simplified auth with role selection.
For production: 2FA login required for clients, firm SSO for attorneys.
"""

from enum import Enum
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from typing import Optional
import hashlib
import secrets

router = APIRouter(tags=["auth"])


class UserRole(str, Enum):
    PROSPECTIVE_CLIENT = "prospective_client"  # Invited by firm for evaluation
    NEW_CLIENT = "new_client"                  # Case accepted, creating account
    EXISTING_CLIENT = "existing_client"        # Verified account, signed contract
    ATTORNEY = "attorney"                      # Legal firm staff
    ADMIN = "admin"                            # System management (future)

    # Backward compat alias
    CLIENT = "client"  # Maps to existing_client


class LoginRequest(BaseModel):
    email: str
    role: UserRole = UserRole.CLIENT
    name: Optional[str] = None
    # In production: password, 2FA token, SSO token
    # In sandbox: role is sufficient


class LoginResponse(BaseModel):
    success: bool
    session_token: str
    role: str
    display_name: str
    redirect_to: str


class SessionInfo(BaseModel):
    session_token: str
    role: UserRole
    email: str
    display_name: str
    created_at: datetime
    case_id: Optional[str] = None


# In-memory session store (replace with DB/Redis in production)
_sessions: dict[str, SessionInfo] = {}


def _create_token() -> str:
    return secrets.token_urlsafe(32)


@router.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """
    Authenticate and get a session token.

    Sandbox mode: accepts any email + role (no password required).
    Production mode: would validate credentials + 2FA.

    Returns a redirect URL based on role:
      - client → /client
      - attorney → /attorney
    """
    token = _create_token()
    display_name = body.name or body.email.split("@")[0]

    session = SessionInfo(
        session_token=token,
        role=body.role,
        email=body.email,
        display_name=display_name,
        created_at=datetime.now(timezone.utc),
    )
    _sessions[token] = session

    redirect_map = {
        UserRole.PROSPECTIVE_CLIENT: "/prospective",
        UserRole.NEW_CLIENT: "/new-client",
        UserRole.EXISTING_CLIENT: "/client",
        UserRole.CLIENT: "/client",       # backward compat
        UserRole.ATTORNEY: "/attorney",
        UserRole.ADMIN: "/attorney",      # admin sees attorney view + extras
    }

    return LoginResponse(
        success=True,
        session_token=token,
        role=body.role.value,
        display_name=display_name,
        redirect_to=redirect_map.get(body.role, "/client"),
    )


@router.get("/auth/session")
def get_session(token: str):
    """Validate a session token and return session info."""
    session = _sessions.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return {
        "success": True,
        "role": session.role.value,
        "email": session.email,
        "display_name": session.display_name,
        "case_id": session.case_id,
    }


@router.post("/auth/logout")
def logout(token: str):
    """End a session."""
    _sessions.pop(token, None)
    return {"success": True}


def get_session_from_token(token: str) -> Optional[SessionInfo]:
    """Helper for other routers to validate sessions."""
    return _sessions.get(token)


def set_session_case(token: str, case_id: str):
    """Associate a case ID with a session."""
    session = _sessions.get(token)
    if session:
        session.case_id = case_id
