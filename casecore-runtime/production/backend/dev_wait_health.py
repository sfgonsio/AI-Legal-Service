"""
Poll backend /health until it answers or we time out.
"""
import os
import sys
import time

import httpx

PORT = int(os.getenv("DEV_PORT", "8765"))
URL = f"http://127.0.0.1:{PORT}/health"
DEADLINE = time.time() + 30.0


def main() -> int:
    last_err = None
    while time.time() < DEADLINE:
        try:
            r = httpx.get(URL, timeout=1.0)
            if r.status_code == 200:
                print(f"OK backend listening at {URL}")
                print(f"OK response: {r.json()}")
                return 0
        except Exception as e:
            last_err = e
        time.sleep(0.5)
    print(f"FAIL backend not listening after 30s. last error: {last_err}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
