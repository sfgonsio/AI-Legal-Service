"""
SANDBOX Launcher — Play, Test, Perfect

Starts the INTAKE_ENGINE in full sandbox isolation.
All data goes to data/sandbox/ — completely separate from production.

Usage:
  python launch_sandbox.py              # Start sandbox server
  python launch_sandbox.py --reset      # Wipe ALL sandbox data and start fresh
  python launch_sandbox.py --status     # Show what's in the sandbox

IMPORTANT: Nothing from sandbox carries to production. Ever.
"""

import os
import sys
import argparse

# Force sandbox environment BEFORE any other imports
os.environ["CASECORE_ENV"] = "sandbox"

# Add project paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "config"))


def main():
    parser = argparse.ArgumentParser(description="CaseCore SANDBOX Launcher")
    parser.add_argument("--reset", action="store_true", help="Wipe ALL sandbox data and start fresh")
    parser.add_argument("--status", action="store_true", help="Show sandbox data status")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on (default: 8000)")
    args = parser.parse_args()

    from config.environments import (
        get_data_paths, ensure_data_dirs, wipe_sandbox,
        Environment,
    )

    paths = get_data_paths(Environment.SANDBOX)

    # Handle --status
    if args.status:
        print("\n  SANDBOX STATUS")
        print("  " + "=" * 50)
        for key, value in paths.items():
            if key in ("environment", "label", "is_sandbox", "banner"):
                continue
            if isinstance(value, str) and os.path.isdir(value):
                count = sum(len(files) for _, _, files in os.walk(value))
                print(f"  {key:25s} {count:5d} files")
            elif isinstance(value, str) and os.path.isfile(value.replace("sqlite:///", "")):
                size = os.path.getsize(value.replace("sqlite:///", ""))
                print(f"  {key:25s} {size:,d} bytes")
            else:
                print(f"  {key:25s} (empty)")
        print()
        return

    # Handle --reset
    if args.reset:
        print("\n  SANDBOX RESET")
        print("  " + "=" * 50)
        confirm = input("  This will DELETE ALL sandbox data. Type 'RESET' to confirm: ")
        if confirm.strip() != "RESET":
            print("  Cancelled.")
            return
        result = wipe_sandbox()
        print("\n  Wiped:")
        for key, info in result.items():
            files = info.get("files_removed", 0)
            if files or info.get("removed"):
                print(f"    {key}: {files} files removed")
        print("\n  Sandbox is clean. Starting fresh...\n")

    # Ensure directories exist
    ensure_data_dirs(Environment.SANDBOX)

    # Load .env
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
    except ImportError:
        pass

    # Start server
    import uvicorn
    from launch_intake import app  # reuse the same app

    print("\n" + "=" * 60)
    print("  CASECORE INTAKE_ENGINE — SANDBOX MODE")
    print("  " + "-" * 56)
    print("  All data isolated to: data/sandbox/")
    print("  Nothing carries to production.")
    print("  Use --reset to wipe and start fresh.")
    print("=" * 60)
    print(f"\n  Login:     http://localhost:{args.port}/")
    print(f"  Client:    http://localhost:{args.port}/client")
    print(f"  Attorney:  http://localhost:{args.port}/attorney")
    print(f"  API Docs:  http://localhost:{args.port}/docs")
    print(f"  Health:    http://localhost:{args.port}/health")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=args.port, reload=False)


if __name__ == "__main__":
    main()
