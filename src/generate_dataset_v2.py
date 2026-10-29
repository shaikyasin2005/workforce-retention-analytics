
from pathlib import Path
import sqlite3
import random
import hashlib
from datetime import date, timedelta

# --------------------------------------------------
# Project configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"

RANDOM_SEED = 20261022
EMPLOYEE_COUNT = 10_000
AS_OF_DATE = date(2026, 10, 28)
HISTORY_MONTHS = 24
SURVEY_MISSINGNESS_RATE = 0.15
WORKLOAD_MISSINGNESS_RATE = 0.10
SURVEY_VERSION = "survey-v1"


# --------------------------------------------------
# Synthetic master data
# --------------------------------------------------

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


def stable_id(prefix, *parts):
    """Return a deterministic ID based on its input components."""
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def employee_values(number):
    """
    Generate deterministic employee attributes.

    Existing employees 1-100 are preserved. Their original values
    are not overwritten by this function.
    """
    rng = random.Random(f"{RANDOM_SEED}:{number}")

    employee_id = f"EMP-{number:06d}"
    role_id, _, _ = rng.choice(ROLES)
    team_id, _, _ = rng.choice(TEAMS)
    band_id, _, _, _, _ = rng.choice(COMPENSATION_BANDS)

    earliest_date = AS_OF_DATE - timedelta(days=1400)
    latest_date = AS_OF_DATE - timedelta(days=30)
    days_range = (latest_date - earliest_date).days

    start_date = earliest_date + timedelta(
        days=rng.randint(0, days_range)
    )

    return (
        employee_id,
        start_date.isoformat(),
        role_id,
        team_id,
        band_id,
        "Active",
        AS_OF_DATE.isoformat(),
    )


def generate_master_records(cursor):
    """Insert role, team, and compensation master records."""
    for role_id, role_name, category in ROLES:
        cursor.execute(
            """
            INSERT OR IGNORE INTO Role
                (role_id, role_name, role_category, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (role_id, role_name, category, AS_OF_DATE.isoformat()),
        )

    for team_id, team_name, department in TEAMS:
        cursor.execute(
            """
            INSERT OR IGNORE INTO Team
                (team_id, team_name, department_name, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (team_id, team_name, department, AS_OF_DATE.isoformat()),
        )

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
            (band_id, band_name, level, minimum, maximum),
        )


def generate_employees(cursor):
    """
    Preserve existing employees and insert missing employee records.

    Initial assignment and compensation history are created only
    for employees that do not already exist.
    """
    existing_ids = {
        row[0]
        for row in cursor.execute(
            "SELECT employee_id FROM Employee"
        ).fetchall()
    }

    inserted = 0
    skipped = 0

    for number in range(1, EMPLOYEE_COUNT + 1):
        (
            employee_id,
            start_date,
            role_id,
            team_id,
            band_id,
            status,
            created_at,
        ) = employee_values(number)

        if employee_id in existing_ids:
            skipped += 1
            continue

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
                start_date,
                role_id,
                team_id,
                band_id,
                status,
                created_at,
            ),
        )

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
                stable_id("ASN", employee_id, "initial"),
                employee_id,
                role_id,
                team_id,
                start_date,
                "InitialAssignment",
                created_at,
            ),
        )

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
                stable_id("COMP", employee_id, "initial"),
                employee_id,
                band_id,
                start_date,
                "InitialAssignment",
                created_at,
            ),
        )

        inserted += 1

    return inserted, skipped


def generate_longitudinal_history(cursor):
    """Generate deterministic monthly tenure, survey, and workload data."""

    if not 0 <= SURVEY_MISSINGNESS_RATE <= 1:
        raise ValueError("SURVEY_MISSINGNESS_RATE must be between 0 and 1.")

    if not 0 <= WORKLOAD_MISSINGNESS_RATE <= 1:
        raise ValueError("WORKLOAD_MISSINGNESS_RATE must be between 0 and 1.")

    # Generate 24 calendar months, from November 2024 to October 2026.
    months = []
    year, month = 2024, 11

    for _ in range(HISTORY_MONTHS):
        months.append(date(year, month, 1))
        month += 1

        if month == 13:
            month = 1
            year += 1

    employees = cursor.execute(
        """
        SELECT employee_id, employment_start_date
        FROM Employee
        ORDER BY employee_id
        """
    ).fetchall()

    tenure_inserted = 0
    survey_inserted = 0
    workload_inserted = 0

    for employee_id, start_text in employees:
        employment_start = date.fromisoformat(start_text)

        for month_start_date in months:
            if month_start_date > AS_OF_DATE:
                continue

            # Find the final day of the current month.
            if month_start_date.month == 12:
                next_month = date(month_start_date.year + 1, 1, 1)
            else:
                next_month = date(
                    month_start_date.year,
                    month_start_date.month + 1,
                    1,
                )

            month_end = min(
                next_month - timedelta(days=1),
                AS_OF_DATE,
            )

            # Do not create records before the employee was hired.
            if employment_start > month_end:
                continue

            observation_date = max(
                month_start_date,
                employment_start,
            )

            rng = random.Random(
                f"{RANDOM_SEED}:{employee_id}:{month_start_date.isoformat()}"
            )

            tenure_days = (observation_date - employment_start).days

            cursor.execute(
                """
                INSERT OR IGNORE INTO TenureSnapshot (
                    snapshot_id,
                    employee_id,
                    snapshot_date,
                    tenure_days,
                    employment_status,
                    observation_period
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    stable_id(
                        "TENURE",
                        employee_id,
                        observation_date.isoformat(),
                    ),
                    employee_id,
                    observation_date.isoformat(),
                    tenure_days,
                    "Active",
                    month_start_date.strftime("%Y-%m"),
                ),
            )
            tenure_inserted += cursor.rowcount

            # Survey response status and score.
            survey_draw = rng.random()

            if survey_draw < SURVEY_MISSINGNESS_RATE:
                response_status = "Missing"
                engagement_score = None
            elif survey_draw < SURVEY_MISSINGNESS_RATE + 0.05:
                response_status = "Partial"
                engagement_score = (
                    round(rng.uniform(1, 5), 1)
                    if rng.random() < 0.5
                    else None
                )
            else:
                response_status = "Completed"
                engagement_score = round(
                    rng.uniform(1, 5), 1
                )

            cursor.execute(
                """
                INSERT OR IGNORE INTO EngagementSurvey (
                    survey_id,
                    employee_id,
                    survey_date,
                    engagement_score,
                    response_status,
                    survey_version
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    stable_id(
                        "SURVEY",
                        employee_id,
                        observation_date.isoformat(),
                        SURVEY_VERSION,
                    ),
                    employee_id,
                    observation_date.isoformat(),
                    engagement_score,
                    response_status,
                    SURVEY_VERSION,
                ),
            )
            survey_inserted += cursor.rowcount

            # Workload: high workload is not itself evidence of attrition.
            if rng.random() < WORKLOAD_MISSINGNESS_RATE:
                hours = None
                pressure = None
                category = "Unknown"
                source = "SyntheticManagerEstimate"
            else:
                # Include both ordinary and benign high-workload cases.
                if rng.random() < 0.15:
                    hours = round(rng.uniform(50, 65), 1)
                else:
                    hours = round(rng.uniform(30, 49.9), 1)

                pressure = round(rng.uniform(10, 95), 1)

                if hours >= 50 or pressure >= 70:
                    category = "High"
                elif hours < 35 and pressure < 35:
                    category = "Low"
                else:
                    category = "Normal"

                source = rng.choice(
                    [
                        "SyntheticSchedule",
                        "SyntheticSurvey",
                        "SyntheticManagerEstimate",
                    ]
                )

            period_start = observation_date.isoformat()
            period_end = month_end.isoformat()

            cursor.execute(
                """
                INSERT OR IGNORE INTO WorkloadSnapshot (
                    workload_snapshot_id,
                    employee_id,
                    period_start,
                    period_end,
                    workload_hours_per_week,
                    workload_pressure_score,
                    workload_category,
                    measurement_source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stable_id(
                        "WORKLOAD",
                        employee_id,
                        period_start,
                        period_end,
                    ),
                    employee_id,
                    period_start,
                    period_end,
                    hours,
                    pressure,
                    category,
                    source,
                ),
            )
            workload_inserted += cursor.rowcount

    print("Monthly history generation completed.")
    print(f"New tenure snapshots: {tenure_inserted:,}")
    print(f"New engagement surveys: {survey_inserted:,}")
    print(f"New workload snapshots: {workload_inserted:,}")


def generate_promotion_history(cursor):
    """Generate deterministic synthetic promotion and role-change events."""

    employees = cursor.execute(
        """
        SELECT employee_id, employment_start_date, initial_role_id
        FROM Employee
        ORDER BY employee_id
        """
    ).fetchall()

    inserted = 0

    for employee_id, start_text, initial_role_id in employees:
        rng = random.Random(
            f"{RANDOM_SEED}:{employee_id}:promotion"
        )

        # Some employees have no promotion event.
        if rng.random() >= 0.20:
            continue

        start_date = date.fromisoformat(start_text)

        earliest_event = max(
            start_date + timedelta(days=180),
            date(2024, 11, 1),
        )

        latest_event = min(
            AS_OF_DATE,
            date(2026, 10, 1),
        )

        if earliest_event > latest_event:
            continue

        available_days = (latest_event - earliest_event).days
        event_date = earliest_event + timedelta(
            days=rng.randint(0, available_days)
        )

        eligible_roles = [
            role for role in ROLES
            if role[0] != initial_role_id
        ]

        if not eligible_roles:
            continue

        new_role_id, new_role_name, _ = rng.choice(eligible_roles)

        progression_type = rng.choices(
            ["Promotion", "LateralMove", "CareerLevelChange", "RoleExpansion"],
            weights=[50, 25, 15, 10],
            k=1,
        )[0]

        cursor.execute(
            """
            INSERT OR IGNORE INTO PromotionHistory (
                promotion_event_id,
                employee_id,
                event_date,
                previous_role_id,
                new_role_id,
                progression_type,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stable_id(
                    "PROMO",
                    employee_id,
                    event_date.isoformat(),
                ),
                employee_id,
                event_date.isoformat(),
                initial_role_id,
                new_role_id,
                progression_type,
                "Synthetic event generated for project testing.",
            ),
        )

        inserted += cursor.rowcount

    print(f"New promotion history events: {inserted:,}")

def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    if EMPLOYEE_COUNT < 1:
        raise ValueError("EMPLOYEE_COUNT must be positive.")

    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        with connection:
            cursor = connection.cursor()

            generate_master_records(cursor)
            inserted, skipped = generate_employees(cursor)
            generate_longitudinal_history(cursor)
            generate_promotion_history(cursor)

            total = cursor.execute(
                "SELECT COUNT(*) FROM Employee"
            ).fetchone()[0]

            history_count = cursor.execute(
                "SELECT COUNT(*) FROM EmployeeAssignmentHistory"
            ).fetchone()[0]

            compensation_count = cursor.execute(
                "SELECT COUNT(*) FROM EmployeeCompensationHistory"
            ).fetchone()[0]

            if total < EMPLOYEE_COUNT:
                raise RuntimeError(
                    f"Expected at least {EMPLOYEE_COUNT} employees; "
                    f"found {total}."
                )

        print("Employee generation completed.")
        print(f"New employees inserted: {inserted:,}")
        print(f"Existing employee IDs skipped: {skipped:,}")
        print(f"Total employees in database: {total:,}")
        print(f"Assignment history rows: {history_count:,}")
        print(f"Compensation history rows: {compensation_count:,}")
        print("Database transaction: COMMITTED")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
