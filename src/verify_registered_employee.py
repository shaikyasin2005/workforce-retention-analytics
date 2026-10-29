
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"

employee_id = "EMP-010003"

connection = sqlite3.connect(
    f"file:{DATABASE_PATH.as_posix()}?mode=ro",
    uri=True,
)

try:
    employee = connection.execute(
        """
        SELECT employee_id, employment_start_date,
               employment_status, initial_role_id, initial_team_id
        FROM Employee
        WHERE employee_id = ?
        """,
        (employee_id,),
    ).fetchone()

    if employee is None:
        print(f"Employee {employee_id} was not found.")
    else:
        assignment_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM EmployeeAssignmentHistory
            WHERE employee_id = ?
            """,
            (employee_id,),
        ).fetchone()[0]

        compensation_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM EmployeeCompensationHistory
            WHERE employee_id = ?
            """,
            (employee_id,),
        ).fetchone()[0]

        print("REGISTERED EMPLOYEE VERIFICATION")
        print("=" * 40)
        print("Employee record:", employee)
        print("Assignment history:", assignment_count)
        print("Compensation history:", compensation_count)

finally:
    connection.close()
