from pathlib import Path
import sqlite3
import random
from datetime import date, timedelta

# Project configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"

RANDOM_SEED = 20261022
EMPLOYEE_COUNT = 100  # Small test dataset first

random.seed(RANDOM_SEED)

# Synthetic master data
ROLES = [
    ("ROLE-001", "Software Developer", "Engineering"),
    ("ROLE-002", "Data Analyst", "Analytics"),
    ("ROLE-003", "Data Engineer", "Engineering"),
    ("ROLE-004", "QA Engineer", "Quality Assurance"),
    ("ROLE-005", "Project Manager", "Management"),
]

TEAMS = [
    ("TEAM-001", "Platform Team", "Engineering"),
    ("TEAM-002", "Data Team", "Analytics"),
    ("TEAM-003", "Quality Team", "Quality Assurance"),
    ("TEAM-004", "Delivery Team", "Operations"),
]

COMPENSATION_BANDS = [
    ("BAND-001", "Junior", 1, 25000, 45000),
    ("BAND-002", "Mid-level", 2, 45001, 75000),
    ("BAND-003", "Senior", 3, 75001, 120000),
    ("BAND-004", "Lead", 4, 120001, 180000),
]


def generate_employees():
    """Insert synthetic master records and employee records."""

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        with connection:
            cursor = connection.cursor()

            # Create role records
            for role_id, role_name, category in ROLES:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO Role
                    (role_id, role_name, role_category, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (role_id, role_name, category, date.today().isoformat()),
                )

            # Create team records
            for team_id, team_name, department in TEAMS:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO Team
                    (team_id, team_name, department_name, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (team_id, team_name, department, date.today().isoformat()),
                )

            
            # Create compensation bands
            for band_id, band_name, level, minimum, maximum in COMPENSATION_BANDS:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO CompensationBand (
                        compensation_band_id,
                        band_name,
                        level_order,
                        currency_code,
                        minimum_amount,
                        maximum_amount
                    )
                    VALUES (?, ?, ?, 'INR', ?, ?)
                    """,
                    (
                        band_id,
                        band_name,
                        level,
                        minimum,
                        maximum,
                    ),
                )

    
            # Generate synthetic employees
            today = date.today()

            for number in range(1, EMPLOYEE_COUNT + 1):
                employee_id = f"EMP-{number:06d}"

                role_id, _, _ = random.choice(ROLES)
                team_id, _, _ = random.choice(TEAMS)
                band_id, _, _, _, _ = random.choice(COMPENSATION_BANDS)

                # Generate a valid employment start date
                start_date = today - timedelta(
                    days=random.randint(30, 1400)
                )
                start_date_text = start_date.isoformat()
                today_text = today.isoformat()

                # Insert employee with all required fields
                cursor.execute(
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
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        employee_id,
                        start_date_text,
                        role_id,
                        team_id,
                        band_id,
                        "Active",
                        today_text,
                    ),
                )

                # Insert initial role and team assignment
                cursor.execute(
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
                    VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
                    """,
                    (
                        f"ASN-{number:06d}-001",
                        employee_id,
                        role_id,
                        team_id,
                        start_date_text,
                        "InitialAssignment",
                        today_text,
                    ),
                )

                # Insert initial compensation history
                cursor.execute(
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
                    VALUES (?, ?, ?, ?, NULL, ?, ?)
                    """,
                    (
                        f"COMP-{number:06d}-001",
                        employee_id,
                        band_id,
                        start_date_text,
                        "InitialAssignment",
                        today_text,
                    ),
                )

        print(f"Employees created: {EMPLOYEE_COUNT}")
        print(f"Database: {DATABASE_PATH}")

    finally:
        connection.close()



if __name__ == "__main__":
    generate_employees()
