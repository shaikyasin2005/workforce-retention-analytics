from pathlib import Path
import sqlite3
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"

SCORING_DATE = "2026-07-30"


def main():
    with sqlite3.connect(DATABASE_PATH) as connection:
        queries = {
            "Engagement": """
                SELECT engagement_score
                FROM EngagementSurvey
                WHERE survey_date <= ?
                  AND engagement_score IS NOT NULL
            """,
            "Workload pressure": """
                SELECT workload_pressure_score
                FROM WorkloadSnapshot
                WHERE period_end <= ?
                  AND workload_pressure_score IS NOT NULL
            """,
            "Weekly workload hours": """
                SELECT workload_hours_per_week
                FROM WorkloadSnapshot
                WHERE period_end <= ?
                  AND workload_hours_per_week IS NOT NULL
            """,
        }

        print("HISTORICAL FEATURE PATTERNS")
        print("=" * 45)

        for name, query in queries.items():
            values = pd.read_sql_query(
                query, connection, params=(SCORING_DATE,)
            ).iloc[:, 0]

            print(f"\n{name}")
            print(f"Available records: {len(values):,}")

            if values.empty:
                print("No historical values available.")
                continue

            print(f"Unique values: {values.nunique():,}")
            print(f"Minimum: {values.min():.2f}")
            print(f"Maximum: {values.max():.2f}")
            print(f"Average: {values.mean():.2f}")


if __name__ == "__main__":
    main()