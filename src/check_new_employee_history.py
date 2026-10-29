import sqlite3
from pathlib import Path

database_path = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "workforce_retention.db"
)

employee_id = "EMP-010002"

connection = sqlite3.connect(database_path)

try:
    tables = {
        "Employee": "employee_id",
        "EmployeeAssignmentHistory": "employee_id",
        "EmployeeCompensationHistory": "employee_id",
        "TenureSnapshot": "employee_id",
        "EngagementSurvey": "employee_id",
        "WorkloadSnapshot": "employee_id",
        "PromotionHistory": "employee_id",
        "AttritionOutcome": "employee_id",
    }

    print(f"History check for {employee_id}")
    print("-" * 45)

    for table, column in tables.items():
        count = connection.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {column} = ?",
            (employee_id,),
        ).fetchone()[0]

        print(f"{table}: {count}")

finally:
    connection.close()