from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"
SCORING_DATE = "2026-07-30"

with sqlite3.connect(DATABASE_PATH) as connection:
    print("SCORING COHORT CHECK")

    query = """
        SELECT
            COUNT(*) AS total_employees,
            SUM(
                CASE
                    WHEN employment_start_date <= ?
                    THEN 1 ELSE 0
                END
            ) AS hired_by_scoring_date,
            SUM(
                CASE
                    WHEN employment_status = 'Active'
                    THEN 1 ELSE 0
                END
            ) AS currently_active
        FROM Employee
    """

    print(connection.execute(query, (SCORING_DATE,)).fetchone())

    query = """
        SELECT
            outcome_status,
            COUNT(*)
        FROM AttritionOutcome
        WHERE scoring_date = ?
        GROUP BY outcome_status
        ORDER BY outcome_status
    """

    print("\nOUTCOME STATUS COUNTS")
    for row in connection.execute(query, (SCORING_DATE,)):
        print(row)


        
print("\nASSIGNMENT HISTORY CHECK")

with sqlite3.connect(DATABASE_PATH) as connection:
    query = """
        SELECT COUNT(DISTINCT employee_id)
        FROM EmployeeAssignmentHistory
        WHERE effective_from <= ?
          AND (effective_to IS NULL OR effective_to >= ?)
    """

    count = connection.execute(
        query,
        (SCORING_DATE, SCORING_DATE)
    ).fetchone()[0]

    print("Employees with an assignment on scoring date:", count)
