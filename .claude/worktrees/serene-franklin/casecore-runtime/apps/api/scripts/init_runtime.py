#!/usr/bin/env python3
"""
Initialize CaseCore runtime environment
Idempotent: creates schema only (no seeding)
Called once per deployment before starting the server
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from casecore.backend.database import init_db, AsyncSessionLocal
from casecore.backend.runtime_config import initialize_runtime_config


async def main():
    """Initialize runtime: read config, create schema, verify DB connectivity"""
    print("[init_runtime] Starting...")

    # Initialize runtime config
    try:
        runtime_config = initialize_runtime_config()
        print(f"[init_runtime] ✓ Runtime config initialized: {runtime_config.name.value}")
    except Exception as e:
        print(f"[init_runtime] ✗ Failed to initialize runtime config: {e}")
        sys.exit(1)

    # Initialize database schema
    try:
        await init_db()
        print(f"[init_runtime] ✓ Database schema initialized")
    except Exception as e:
        print(f"[init_runtime] ✗ Failed to initialize database: {e}")
        sys.exit(1)

    # Verify database connectivity
    try:
        async with AsyncSessionLocal() as db:
            from casecore.backend.models import Case
            from sqlalchemy import select, func
            result = await db.execute(select(func.count(Case.id)))
            case_count = result.scalar() or 0
            print(f"[init_runtime] ✓ Database connectivity verified ({case_count} cases present)")
    except Exception as e:
        print(f"[init_runtime] ✗ Failed to verify database: {e}")
        sys.exit(1)

    # Print capabilities for this runtime
    print(f"[init_runtime] Capabilities for {runtime_config.name.value}:")
    for cap, enabled in runtime_config.capabilities.items():
        status = "✓ ENABLED" if enabled else "✗ DISABLED"
        print(f"  {cap}: {status}")

    print("[init_runtime] ✓ Initialization complete")


if __name__ == "__main__":
    asyncio.run(main())
