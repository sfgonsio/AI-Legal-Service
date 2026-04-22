"""Alembic environment.

Derives a synchronous SQLAlchemy URL from the runtime's DATABASE_URL so
Alembic can run without touching the async engine in database.py.

Supported mappings:
  sqlite+aiosqlite:///path   -> sqlite:///path
  postgresql+asyncpg://...   -> postgresql+psycopg2://...  (falls back to bare postgresql://)

If DATABASE_URL is not set, falls back to the sqlalchemy.url in alembic.ini
(currently sqlite:///./casecore.db).
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make the backend directory importable so we can load Base and core_models.
_HERE = Path(__file__).resolve().parent
_BACKEND_DIR = _HERE.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))


def _derive_sync_url(url: str | None) -> str | None:
    """Convert an async runtime URL into a sync URL suitable for Alembic."""
    if not url:
        return None
    if url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    return url


# ---------------------------------------------------------------------------
# database.py instantiates an async engine at import time, so it requires an
# async driver in DATABASE_URL. Alembic itself runs sync. We sidestep that by
# temporarily forcing an async URL during the database.py import, then restoring
# the caller-supplied URL (converted to sync form) for Alembic's own engine.
# The async engine created by database.py during this import is never used.
# ---------------------------------------------------------------------------
_caller_url = os.environ.get("DATABASE_URL")
_sync_url = _derive_sync_url(_caller_url)

# Force a safe async URL during import. Use in-memory sqlite for speed.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from database import Base  # noqa: E402
import models  # noqa: F401,E402  (legacy War Room tables; not owned by this migration set)
import core_models  # noqa: F401,E402  (hardened truth-layer tables — Wave 1 + Wave 2)

# Restore the caller's URL (may be None) now that the import is done.
if _caller_url is None:
    os.environ.pop("DATABASE_URL", None)
else:
    os.environ["DATABASE_URL"] = _caller_url


config = context.config

# If a sync URL can be derived from the caller's DATABASE_URL, override
# alembic.ini's default. Otherwise the alembic.ini default is used.
if _sync_url:
    config.set_main_option("sqlalchemy.url", _sync_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a live connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=url.startswith("sqlite"),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a real connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
