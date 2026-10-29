
from pathlib import Path
import sqlite3
import hashlib
from datetime import date, datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"

EMPLOYEE_ID = "EMP-010002"
SURVEY_VERSION = "v1"

# Reproducible synthetic values for this demonstration employee.
# Change this seed only if you intentionally want a different history.
SEED = 20261029


def stable_id(prefix, *parts):
    """Generate deterministic IDs from input values."""
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def deterministic_number(*parts):
    """Return a reproducible integer from the supplied values."""
    raw = "|".join(str(part) for part in (SEED, *parts))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def get_workload_category(hours, pressure):
    """Classify workload using documented demonstration rules."""
    if hours is None or pressure is None:
        return "Unknown"

    if pressure >= 75 or hours >= 50:
        return "High"

    if pressure < 35 and hours < 38:
        return "Low"

    return "Normal"


def generate_history():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    today = date.today()
    today_text = today.isoformat()
    timestamp = datetime.now().isoformat(timespec="seconds")

    counts = {
        "tenure": 0,
        "surveys": 0,
        "workloads": 0,
        "audit": 0,
    }

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        employee = connection.execute(
            """
            SELECT employment_start_date, employment_status
            FROM Employee
            WHERE employee_id = ?
            """,
            (EMPLOYEE_ID,),
        ).fetchone()

        if employee is None:
            raise ValueError(
                f"Employee {EMPLOYEE_ID} does not exist."
            )

        start_text, employment_status = employee
        start_date = date.fromisoformat(start_text)

        if start_date > today:
            raise ValueError(
                "Employment start date is in the future."
            )

        if employment_status == "Terminated":
            raise ValueError(
                "This script does not generate history "
                "for terminated employees."
            )

        # Use a single transaction so partial writes are rolled back.
        with connection:
            # 1. Tenure snapshot: at most one for this date.
            existing_tenure = connection.execute(
                """
                SELECT 1
                FROM TenureSnapshot
                WHERE employee_id = ?
                  AND snapshot_date = ?
                LIMIT 1
                """,
                (EMPLOYEE_ID, today_text),
            ).fetchone()

            if not existing_tenure:
                tenure_days = (today - start_date).days

                connection.execute(
                    """
                    INSERT INTO TenureSnapshot (
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
                            "SNAP",
                            EMPLOYEE_ID,
                            today_text,
                        ),
                        EMPLOYEE_ID,
                        today_text,
                        tenure_days,
                        employment_status,
                        today.strftime("%Y-%m"),
                    ),
                )
                counts["tenure"] += 1

            # 2. Monthly survey records, starting in the
            # employee's start month.
            month_start = date(
                start_date.year,
                start_date.month,
                1,
            )

            while month_start <= today:
                survey_date = min(
                    date(
                        month_start.year,
                        month_start.month,
                        28,
                    ),
                    today,
                )
                survey_date_text = survey_date.isoformat()

                existing_survey = connection.execute(
                    """
                    SELECT 1
                    FROM EngagementSurvey
                    WHERE employee_id = ?
                      AND survey_date = ?
                      AND survey_version = ?
                    LIMIT 1
                    """,
                    (
                        EMPLOYEE_ID,
                        survey_date_text,
                        SURVEY_VERSION,
                    ),
                ).fetchone()

                if not existing_survey:
                    choice = deterministic_number(
                        EMPLOYEE_ID,
                        survey_date_text,
                        "survey_status",
                    ) % 10

                    # Explicitly preserve nonresponse.
                    if choice in (0, 1):
                        response_status = "Missing"
                        engagement_score = None
                    else:
                        response_status = "Completed"

                        # Synthetic score between 1 and 5,
                        # deterministic and reproducible.
                        score_value = (
                            deterministic_number(
                                EMPLOYEE_ID,
                                survey_date_text,
                                "engagement_score",
                            )
                            % 41
                        )
                        engagement_score = round(
                            1.0 + score_value / 10.0,
                            1,
                        )

                    connection.execute(
                        """
                        INSERT INTO EngagementSurvey (
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
                                "SURV",
                                EMPLOYEE_ID,
                                survey_date_text,
                                SURVEY_VERSION,
                            ),
                            EMPLOYEE_ID,
                            survey_date_text,
                            engagement_score,
                            response_status,
                            SURVEY_VERSION,
                        ),
                    )
                    counts["surveys"] += 1

                # Move to the first day of the next month.
                if month_start.month == 12:
                    month_start = date(
                        month_start.year + 1,
                        1,
                        1,
                    )
                else:
                    month_start = date(
                        month_start.year,
                        month_start.month + 1,
                        1,
                    )

            # 3. Weekly workload periods, starting on the
            # employment start date and ending no later than today.
            period_start = start_date

            while period_start <= today:
                period_end = min(
                    period_start + timedelta(days=6),
                    today,
                )
                period_start_text = period_start.isoformat()
                period_end_text = period_end.isoformat()

                existing_workload = connection.execute(
                    """
                    SELECT 1
                    FROM WorkloadSnapshot
                    WHERE employee_id = ?
                      AND period_start = ?
                      AND period_end = ?
                    LIMIT 1
                    """,
                    (
                        EMPLOYEE_ID,
                        period_start_text,
                        period_end_text,
                    ),
                ).fetchone()

                if not existing_workload:
                    # Documented synthetic ranges, not actual
                    # employee observations.
                    hours = 35 + (
                        deterministic_number(
                            EMPLOYEE_ID,
                            period_start_text,
                            "hours",
                        )
                        % 16
                    )

                    pressure = (
                        deterministic_number(
                            EMPLOYEE_ID,
                            period_start_text,
                            "pressure",
                        )
                        % 101
                    )

                    category = get_workload_category(
                        hours,
                        pressure,
                    )

                    connection.execute(
                        """
                        INSERT INTO WorkloadSnapshot (
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
                                "WORK",
                                EMPLOYEE_ID,
                                period_start_text,
                                period_end_text,
                            ),
                            EMPLOYEE_ID,
                            period_start_text,
                            period_end_text,
                            float(hours),
                            float(pressure),
                            category,
                            "SyntheticSchedule",
                        ),
                    )
                    counts["workloads"] += 1

                period_start += timedelta(days=7)

            # 4. Record a single audit event for this run if
            # this run inserted any history records.
            total_created = (
                counts["tenure"]
                + counts["surveys"]
                + counts["workloads"]
            )

            if total_created:
                connection.execute(
                    """
                    INSERT INTO AuditLog (
                        audit_event_id,
                        event_timestamp,
                        actor_reference,
                        entity_name,
                        entity_id,
                        action,
                        change_summary,
                        reason
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        stable_id(
                            "AUDIT",
                            EMPLOYEE_ID,
                            today_text,
                            "HISTORY_GENERATION",
                            total_created,
                        ),
                        timestamp,
                        "SYSTEM",
                        "EmployeeHistory",
                        EMPLOYEE_ID,
                        "CREATE",
                        (
                            f"Created {counts['tenure']} tenure "
                            f"snapshot(s), {counts['surveys']} survey "
                            f"record(s), and {counts['workloads']} "
                            "workload record(s)."
                        ),
                        (
                            "Deterministic synthetic demonstration "
                            "history generation."
                        ),
                    ),
                )
                counts["audit"] = 1

    print("EMPLOYEE HISTORY GENERATION COMPLETED")
    print("=" * 45)
    print(f"Employee ID: {EMPLOYEE_ID}")
    print(f"Employment start date: {start_text}")
    print(f"History through: {today_text}")
    print(f"Tenure snapshots created: {counts['tenure']}")
    print(f"Engagement survey records created: {counts['surveys']}")
    print(f"Workload snapshots created: {counts['workloads']}")
    print(f"Audit records created: {counts['audit']}")
    print("Attrition outcomes created: 0")
    print("Existing records were not overwritten.")


if __name__ == "__main__":
    generate_history()
