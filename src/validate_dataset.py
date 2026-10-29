from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"


def main():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    checks = {
        "Employees": """
            SELECT COUNT(*) FROM Employee
        """,
        "Tenure snapshots": """
            SELECT COUNT(*) FROM TenureSnapshot
        """,
        "Engagement surveys": """
            SELECT COUNT(*) FROM EngagementSurvey
        """,
        "Workload snapshots": """
            SELECT COUNT(*) FROM WorkloadSnapshot
        """,
        "Promotion events": """
            SELECT COUNT(*) FROM PromotionHistory
        """,
        "Attrition outcomes": """
            SELECT COUNT(*) FROM AttritionOutcome
        """,
        "Outcomes with invalid date windows": """
            SELECT COUNT(*)
            FROM AttritionOutcome
            WHERE date(outcome_window_end) !=
                  date(scoring_date, '+' || horizon_days || ' days')
        """,
        "Invalid observed attrition labels": """
            SELECT COUNT(*)
            FROM AttritionOutcome
            WHERE outcome_status = 'ObservedAttrition'
              AND (
                  label_voluntary_attrition != 1
                  OR termination_type != 'Voluntary'
                  OR termination_date IS NULL
              )
        """,
        "Invalid observed no-attrition labels": """
            SELECT COUNT(*)
            FROM AttritionOutcome
            WHERE outcome_status = 'ObservedNoAttrition'
              AND label_voluntary_attrition != 0
        """,
        "Duplicate outcome keys": """
            SELECT COUNT(*)
            FROM (
                SELECT employee_id, scoring_date, horizon_days, label_version
                FROM AttritionOutcome
                GROUP BY employee_id, scoring_date, horizon_days, label_version
                HAVING COUNT(*) > 1
            )
        """,
    }

    try:
        print("DATASET VALIDATION REPORT")
        print("=" * 45)

        for name, query in checks.items():
            result = connection.execute(query).fetchone()[0]
            print(f"{name}: {result}")

        print("Integrity:", connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0])

        violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()
        print("Foreign-key violations:", violations)

    finally:
        connection.close()


if __name__ == "__main__":
    main()