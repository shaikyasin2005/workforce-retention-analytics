
import sqlite3
import tempfile
import shutil
from pathlib import Path

import employee_service

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"


def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    original_service_path = employee_service.DATABASE_PATH
    temp_dir = None

    try:
        # Create a temporary copy of the production database.
        temp_dir = Path(
            tempfile.mkdtemp(prefix="retention_test_")
        )
        test_database = temp_dir / "test_workforce_retention.db"

        # Use SQLite's backup API for a consistent database copy.
        source = sqlite3.connect(DATABASE_PATH)
        target = sqlite3.connect(test_database)

        try:
            source.backup(target)
        finally:
            target.close()
            source.close()

        # Redirect the registration service to the test database.
        employee_service.DATABASE_PATH = test_database

        roles, teams, bands = employee_service.get_reference_data()

        if not roles or not teams or not bands:
            raise RuntimeError(
                "Role, team, or compensation-band reference data is missing."
            )

        employee_id = employee_service.add_employee(
            employment_start_date="2026-10-29",
            role_id=roles[0][0],
            team_id=teams[0][0],
            compensation_band_id=bands[0][0],
        )

        # Explicitly close the inspection connection.
        connection = sqlite3.connect(test_database)

        try:
            connection.execute("PRAGMA foreign_keys = ON")

            employee = connection.execute(
                """
                SELECT employee_id, employment_start_date,
                       initial_role_id, initial_team_id,
                       initial_compensation_band_id, employment_status
                FROM Employee
                WHERE employee_id = ?
                """,
                (employee_id,),
            ).fetchone()

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

            integrity = connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()[0]

            foreign_key_issues = connection.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()

        finally:
            connection.close()

        print("NEW EMPLOYEE REGISTRATION TEST")
        print("=" * 40)
        print("Employee ID:", employee_id)
        print("Employee record:", employee)
        print("Assignment history:", assignment_count)
        print("Compensation history:", compensation_count)
        print("Integrity:", integrity)
        print("Foreign-key violations:", foreign_key_issues)

        assert employee is not None
        assert assignment_count == 1
        assert compensation_count == 1
        assert integrity == "ok"
        assert not foreign_key_issues

        print("PASS: Employee registration test succeeded.")
        print("The main database was not modified.")

    finally:
        employee_service.DATABASE_PATH = original_service_path

        # Retry cleanup if Windows briefly holds a file handle.
        if temp_dir is not None:
            try:
                shutil.rmtree(temp_dir)
                print("Temporary test files cleaned up.")
            except PermissionError:
                print(
                    "Warning: Close any program using the temporary "
                    "database and remove this folder manually:",
                    temp_dir,
                )


if __name__ == "__main__":
    main()
