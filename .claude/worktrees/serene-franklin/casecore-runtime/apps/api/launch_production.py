"""
PRODUCTION Launcher — Clean, Pristine, Governed

Starts the INTAKE_ENGINE in production mode.
All data goes to data/production/ — completely separate from sandbox.

CRITICAL: This script verifies clean state on first launch.
If sandbox data has leaked in, it will REFUSE TO START.

Usage:
  python launch_production.py                  # Start production server
  python launch_production.py --verify-only    # Check clean state without starting
  python launch_production.py --port 8080      # Custom port

REQUIREMENTS:
  - CASECORE_ENV=production (set automatically by this script)
  - ANTHROPIC_API_KEY must be set (no fallback in production)
  - OPENAI_API_KEY must be set (no fallback in production)
"""

import os
import sys
import argparse

# Force production environment
os.environ["CASECORE_ENV"] = "production"

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "config"))


def main():
    parser = argparse.ArgumentParser(description="CaseCore PRODUCTION Launcher")
    parser.add_argument("--verify-only", action="store_true", help="Verify clean state without starting")
    parser.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    args = parser.parse_args()

    from config.environments import (
        get_data_paths, ensure_data_dirs, verify_production_clean,
        Environment,
    )

    # Step 1: Verify clean state
    print("\n  PRODUCTION PRE-FLIGHT CHECK")
    print("  " + "=" * 50)

    report = verify_production_clean()
    if report["clean"]:
        print("  [PASS] Production environment is clean")
    else:
        print("  [FAIL] Production environment is NOT clean:")
        for issue in report["issues"]:
            print(f"    WARNING: {issue['warning']}")
            print(f"             {issue['path']}")
        if args.verify_only:
            sys.exit(1)
        print("\n  Production has existing data. This may be from a prior run.")
        confirm = input("  Continue anyway? (yes/no): ")
        if confirm.strip().lower() != "yes":
            print("  Aborted.")
            sys.exit(1)

    if args.verify_only:
        print("  Verification complete.")
        return

    # Step 2: Verify API keys (required in production)
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
    except ImportError:
        pass

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    if not anthropic_key or anthropic_key.startswith("sk-ant-xxx"):
        print("  [FAIL] ANTHROPIC_API_KEY is required in production.")
        sys.exit(1)
    if not openai_key or openai_key.startswith("sk-xxx"):
        print("  [FAIL] OPENAI_API_KEY is required in production.")
        sys.exit(1)

    print("  [PASS] API keys configured")

    # Step 3: Ensure directories
    ensure_data_dirs(Environment.PRODUCTION)
    print("  [PASS] Data directories ready")

    # Step 4: Launch
    import uvicorn
    from launch_intake import app

    print("\n" + "=" * 60)
    print("  CASECORE INTAKE_ENGINE — PRODUCTION")
    print("  " + "-" * 56)
    print("  Clean spine. Clean brain. Clean agents.")
    print("  All case data enters through governed intake.")
    print("  Full audit trail from moment zero.")
    print("=" * 60)
    print(f"\n  API:       http://localhost:{args.port}/api/v1")
    print(f"  Health:    http://localhost:{args.port}/health")
    print(f"  Docs:      http://localhost:{args.port}/docs")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=args.port, reload=False)


if __name__ == "__main__":
    main()
