"""
Start uvicorn serving the FastAPI app with proper cwd.

Run:
  python casecore-runtime/production/backend/dev_start_backend.py
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.chdir(HERE)
sys.path.insert(0, str(HERE))

import uvicorn  # noqa: E402

PORT = int(os.getenv("DEV_PORT", "8765"))

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=PORT, reload=False, log_level="info")
