"""Pytest fixtures for the core-data services.

Uses an in-memory async SQLite engine. Tables are created via
Base.metadata.create_all for test speed; the Alembic migrations are verified
separately (see README note). This is deliberate — the tests here are for
service-level read/write behavior, not migration structure verification.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make the backend directory importable.
_HERE = Path(__file__).resolve().parent
_BACKEND_DIR = _HERE.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Force an in-memory async sqlite URL before importing database.py so that the
# runtime async engine is created against the in-memory DB.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from database import Base  # noqa: E402
import models  # noqa: F401,E402
import core_models  # noqa: F401,E402


@pytest_asyncio.fixture
async def async_session() -> AsyncSession:
    """Per-test in-memory sqlite AsyncSession with all tables created."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with SessionLocal() as session:
        yield session
        await session.rollback()
    await engine.dispose()
