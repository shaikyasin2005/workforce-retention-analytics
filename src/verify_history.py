from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"


def main():
    with sqlite3.connect(DATABASE_PATH) as connection:
        checks = {
            "Employees": "SELECT COUNT(*) FROM Employee",
            "Tenure snapshots": "SELECT COUNT(*) FROM TenureSnapshot",
            "Engagement surveys": "SELECT COUNT(*) FROM EngagementSurvey",
            "Workload snapshots": "SELECT COUNT(*) FROM WorkloadSnapshot",
            "Promotion history": "SELECT COUNT(*) FROM PromotionHistory",
            "Attrition outcomes": "SELECT COUNT(*) FROM AttritionOutcome",
            "Missing survey responses": """
                SELECT COUNT(*) FROM EngagementSurvey
                WHERE response_status = 'Missing'
            """,
            "Partial survey responses": """
                SELECT COUNT(*) FROM EngagementSurvey
                WHERE response_status = 'Partial'
            """,
            "Unknown workload records": """
                SELECT COUNT(*) FROM WorkloadSnapshot
                WHERE workload_category = 'Unknown'
            """,
            "High workload records": """
                SELECT COUNT(*) FROM WorkloadSnapshot
                WHERE workload_category = 'High'
            """,
        }

        for label, sql in checks.items():
            count = connection.execute(sql).fetchone()[0]
            print(f"{label}: {count:,}")

        print("Integrity:", connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0])

        violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        print("Foreign-key violations:", violations)


if __name__ == "__main__":
    main()