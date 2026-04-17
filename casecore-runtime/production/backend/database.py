"""
SQLite async database setup with SQLAlchemy
Render-compatible: uses persistent disk at /opt/render/project/src/backend/data/
Local dev: uses ./casecore.db
"""
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Default: local dev. Render sets DATABASE_URL via render.yaml
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./casecore.db")

# Ensure data directory exists for SQLite
if "sqlite" in DATABASE_URL:
    db_path = DATABASE_URL.split("///")[-1]
    db_dir = os.path.dirname(db_path)
    if db_dir:
        Path(db_dir).mkdir(parents=True, exist_ok=True)

# SQLite-specific connect args
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"timeout": 30, "check_same_thread": False}

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    future=True
)

Base = declarative_base()


async def get_db():
    """Dependency for FastAPI routes to get async session"""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Create all tables in database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
