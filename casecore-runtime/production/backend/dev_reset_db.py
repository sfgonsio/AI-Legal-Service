"""
Dev DB reset helper: delete existing casecore.db, recreate schema via init_db().
Does NOT seed. Idempotent.

Run:
  python casecore-runtime/production/backend/dev_reset_db.py
"""
import asyncio
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.chdir(HERE)
sys.path.insert(0, str(HERE))

from database import init_db  # noqa: E402
import models  # noqa: E402,F401  (must import to register tables on Base.metadata)

DB_FILE = HERE / "casecore.db"


async def main():
    # 1. delete existing DB
    if DB_FILE.exists():
        print(f"[reset] deleting existing DB: {DB_FILE}")
        DB_FILE.unlink()
    else:
        print(f"[reset] no existing DB at {DB_FILE} (fresh start)")

    # 2. recreate schema
    print("[reset] running init_db() to create schema...")
    await init_db()
    print(f"[reset] DB created: {DB_FILE}")
    print(f"[reset] DB exists: {DB_FILE.exists()}")
    print(f"[reset] DB size: {DB_FILE.stat().st_size if DB_FILE.exists() else 0} bytes")


if __name__ == "__main__":
    asyncio.run(main())
