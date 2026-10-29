from datetime import date, datetime
from pathlib import Path
import re
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"


def get_reference_data():
    """Load valid roles, teams, and compensation bands."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        roles = connection.execute(
            "SELECT role_id, role_name FROM Role ORDER BY role_name"
        ).fetchall()

        teams = connection.execute(
            "SELECT team_id, team_name FROM Team ORDER BY team_name"
        ).fetchall()

        bands = connection.execute(
            """
            SELECT compensation_band_id, band_name
            FROM CompensationBand
            ORDER BY level_order
            """
        ).fetchall()

    return roles, teams, bands


def _next_id(connection, table, column, prefix):
    """Generate the next numeric ID for a supported table."""
    allowed_tables = {
        ("Employee", "employee_id", "EMP"),
        ("EmployeeAssignmentHistory", "assignment_id", "ASSIGN"),
        (
            "EmployeeCompensationHistory",
            "compensation_history_id",
            "COMP-HIST",
        ),
    }

    if (table, column, prefix) not in allowed_tables:
        raise ValueError("Unsupported ID configuration.")

    rows = connection.execute(
        f"SELECT {column} FROM {table}"
    ).fetchall()

    pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
    highest = 0

    for (existing_id,) in rows:
        match = pattern.fullmatch(existing_id)
        if match:
            highest = max(highest, int(match.group(1)))

    return f"{prefix}-{highest + 1:06d}"


def add_employee(
    employment_start_date,
    role_id,
    team_id,
    compensation_band_id,
):
    """
    Add an employee with initial assignment and compensation history.

    All three records are committed together. If any insert fails,
    the transaction is rolled back.
    """
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    try:
        start_date = date.fromisoformat(employment_start_date)
    except (TypeError, ValueError):
        raise ValueError(
            "Enter a valid employment start date (YYYY-MM-DD)."
        ) from None

    if start_date > date.today():
        raise ValueError("Employment start date cannot be in the future.")

    if not role_id:
        raise ValueError("Please select a role.")

    if not team_id:
        raise ValueError("Please select a team.")

    if not compensation_band_id:
        raise ValueError("Please select a compensation band.")

    now = datetime.now().isoformat(timespec="seconds")
    start_date_text = start_date.isoformat()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")

        # Confirm that the selected reference records exist.
        role_exists = connection.execute(
            "SELECT 1 FROM Role WHERE role_id = ?",
            (role_id,),
        ).fetchone()

        team_exists = connection.execute(
            "SELECT 1 FROM Team WHERE team_id = ?",
            (team_id,),
        ).fetchone()

        band_exists = connection.execute(
            """
            SELECT 1
            FROM CompensationBand
            WHERE compensation_band_id = ?
            """,
            (compensation_band_id,),
        ).fetchone()

        if not role_exists:
            raise ValueError("The selected role does not exist.")

        if not team_exists:
            raise ValueError("The selected team does not exist.")

        if not band_exists:
            raise ValueError(
                "The selected compensation band does not exist."
            )

        # Generate unique IDs while holding the write transaction.
        employee_id = _next_id(
            connection, "Employee", "employee_id", "EMP"
        )

        assignment_id = _next_id(
            connection,
            "EmployeeAssignmentHistory",
            "assignment_id",
            "ASSIGN",
        )

        compensation_id = _next_id(
            connection,
            "EmployeeCompensationHistory",
            "compensation_history_id",
            "COMP-HIST",
        )

        # 1. Create the employee master record.
        connection.execute(
            """
            INSERT INTO Employee (
                employee_id,
                employment_start_date,
                initial_role_id,
                initial_team_id,
                initial_compensation_band_id,
                employment_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, 'Active', ?)
            """,
            (
                employee_id,
                start_date_text,
                role_id,
                team_id,
                compensation_band_id,
                now,
            ),
        )

        # 2. Record the employee's initial role and team.
        connection.execute(
            """
            INSERT INTO EmployeeAssignmentHistory (
                assignment_id,
                employee_id,
                role_id,
                team_id,
                effective_from,
                effective_to,
                change_reason,
                recorded_at
            )
            VALUES (?, ?, ?, ?, ?, NULL, 'InitialAssignment', ?)
            """,
            (
                assignment_id,
                employee_id,
                role_id,
                team_id,
                start_date_text,
                now,
            ),
        )

        # 3. Record the employee's initial compensation band.
        connection.execute(
            """
            INSERT INTO EmployeeCompensationHistory (
                compensation_history_id,
                employee_id,
                compensation_band_id,
                effective_from,
                effective_to,
                change_reason,
                recorded_at
            )
            VALUES (?, ?, ?, ?, NULL, 'InitialAssignment', ?)
            """,
            (
                compensation_id,
                employee_id,
                compensation_band_id,
                start_date_text,
                now,
            ),
        )

        # The connection context commits all three records together.
        # An exception rolls back the transaction automatically.
        return employee_id


if __name__ == "__main__":
    print("Employee service module loaded successfully.")
    print(f"Database: {DATABASE_PATH}")