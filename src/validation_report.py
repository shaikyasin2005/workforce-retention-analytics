from pathlib import Path
import sqlite3
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"
REPORT_PATH = PROJECT_ROOT / "validation_report.txt"


def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    checks = {
        "Employees": "SELECT COUNT(*) FROM Employee",
        "Tenure snapshots": "SELECT COUNT(*) FROM TenureSnapshot",
        "Engagement surveys": "SELECT COUNT(*) FROM EngagementSurvey",
        "Workload snapshots": "SELECT COUNT(*) FROM WorkloadSnapshot",
        "Promotion events": "SELECT COUNT(*) FROM PromotionHistory",
        "Attrition outcomes": "SELECT COUNT(*) FROM AttritionOutcome",
        "Invalid outcome date windows": """
            SELECT COUNT(*) FROM AttritionOutcome
            WHERE date(outcome_window_end) !=
                  date(scoring_date, '+' || horizon_days || ' days')
        """,
        "Invalid observed attrition labels": """
            SELECT COUNT(*) FROM AttritionOutcome
            WHERE outcome_status = 'ObservedAttrition'
              AND (
                  label_voluntary_attrition != 1
                  OR termination_type != 'Voluntary'
                  OR termination_date IS NULL
              )
        """,
        "Invalid observed no-attrition labels": """
            SELECT COUNT(*) FROM AttritionOutcome
            WHERE outcome_status = 'ObservedNoAttrition'
              AND label_voluntary_attrition != 0
        """,
        "Duplicate outcome keys": """
            SELECT COUNT(*) FROM (
                SELECT employee_id, scoring_date, horizon_days, label_version
                FROM AttritionOutcome
                GROUP BY employee_id, scoring_date, horizon_days, label_version
                HAVING COUNT(*) > 1
            )
        """,
    }

    results = []
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        results.append("WORKFORCE RETENTION DATASET VALIDATION")
        results.append(f"Generated at: {datetime.now().isoformat(timespec='seconds')}")
        results.append(f"Database: {DATABASE_PATH}")
        results.append("=" * 55)

        for name, query in checks.items():
            value = connection.execute(query).fetchone()[0]
            results.append(f"{name}: {value}")

        integrity = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]
        foreign_keys = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        results.append(f"SQLite integrity: {integrity}")
        results.append(f"Foreign-key violations: {len(foreign_keys)}")

        if foreign_keys:
            results.append(f"Foreign-key details: {foreign_keys}")

        REPORT_PATH.write_text("\n".join(results) + "\n", encoding="utf-8")

        print("\n".join(results))
        print(f"\nReport saved to: {REPORT_PATH}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()