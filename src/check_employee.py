import sqlite3
from pathlib import Path

database_path = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "workforce_retention.db"
)

employee_id = "EMP-010002"

with sqlite3.connect(database_path) as connection:
    result = connection.execute(
        """
        SELECT employee_id, employment_start_date, employment_status
        FROM Employee
        WHERE employee_id = ?
        """,
        (employee_id,)
    ).fetchone()

    if result:
        print("Employee already exists:")
        print(result)
    else:
        print("Employee not found:", employee_id)