"""
Introspect SQLite schema to verify case-scoped CACI + save-progress tables/columns.
"""
import os
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.chdir(HERE)
DB_FILE = HERE / "casecore.db"

REQUIRED_TABLES = {
    "cases",
    "coas",
    "case_authority_decisions",
    "recompute_events",
    "analysis_runs",
    "case_state_events",
}

REQUIRED_CASE_COLUMNS = {
    "save_state",
    "last_saved_at",
    "last_submitted_at",
    "processing_started_at",
    "processing_finished_at",
    "review_required_count",
    "current_analysis_run_id",
    "last_error_detail",
}

REQUIRED_COA_COLUMNS = {
    "authority_decision_id",
    "authority_pinned_record_id",
    "authority_effective_grounding",
}


def main() -> int:
    if not DB_FILE.exists():
        print(f"FAIL: DB not found at {DB_FILE}")
        return 2

    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        print(f"[schema] tables: {sorted(tables)}")

        missing_tables = REQUIRED_TABLES - tables
        if missing_tables:
            print(f"FAIL: missing tables: {sorted(missing_tables)}")
            return 3

        cur.execute("PRAGMA table_info(cases)")
        case_cols = {row[1] for row in cur.fetchall()}
        print(f"[schema] cases columns: {sorted(case_cols)}")
        missing_case = REQUIRED_CASE_COLUMNS - case_cols
        if missing_case:
            print(f"FAIL: missing cases columns: {sorted(missing_case)}")
            return 4

        cur.execute("PRAGMA table_info(coas)")
        coa_cols = {row[1] for row in cur.fetchall()}
        print(f"[schema] coa columns: {sorted(coa_cols)}")
        missing_cols = REQUIRED_COA_COLUMNS - coa_cols
        if missing_cols:
            print(f"FAIL: missing COA columns: {sorted(missing_cols)}")
            return 5

        cur.execute("PRAGMA table_info(analysis_runs)")
        run_cols = {row[1] for row in cur.fetchall()}
        print(f"[schema] analysis_runs columns: {sorted(run_cols)}")

        cur.execute("PRAGMA table_info(case_state_events)")
        ev_cols = {row[1] for row in cur.fetchall()}
        print(f"[schema] case_state_events columns: {sorted(ev_cols)}")

        print("PASS: required schema present")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
