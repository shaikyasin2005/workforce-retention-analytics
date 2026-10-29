from pathlib import Path
import sqlite3

project_root = Path(__file__).resolve().parent.parent
database_path = project_root / "data" / "workforce_retention.db"

scoring_date = "2026-07-30"

with sqlite3.connect(database_path) as connection:
    total = connection.execute(
        "SELECT COUNT(*) FROM Employee"
    ).fetchone()[0]

    started_by_date = connection.execute(
        """
        SELECT COUNT(*)
        FROM Employee
        WHERE employment_start_date <= ?
        """,
        (scoring_date,),
    ).fetchone()[0]

    eligible_outcomes = connection.execute(
        """
        SELECT COUNT(DISTINCT employee_id)
        FROM AttritionOutcome
        WHERE scoring_date = ?
          AND horizon_days = 90
          AND label_version = 'v2'
          AND outcome_status IN (
              'ObservedAttrition',
              'ObservedNoAttrition'
          )
          AND label_voluntary_attrition IN (0, 1)
        """,
        (scoring_date,),
    ).fetchone()[0]

print("Total employees:", total)
print("Started by scoring date:", started_by_date)
print("Employees with eligible outcomes:", eligible_outcomes)
print("Database check completed.")