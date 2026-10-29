from pathlib import Path
import sqlite3
import hashlib
import random
import math
from datetime import date, timedelta


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"

RANDOM_SEED = 20261022
AS_OF_DATE = date(2026, 10, 28)
SCORING_DATE = date(2026, 7, 30)
HORIZON_DAYS = 90
LABEL_VERSION = "v2"
VOLUNTARY_ATTRITION_RATE = 0.10


def stable_id(prefix, *parts):
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def clamp(value, low, high):
    return max(low, min(high, value))


def generate_outcomes():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    if not 0 < VOLUNTARY_ATTRITION_RATE < 1:
        raise ValueError("Attrition rate must be between 0 and 1.")

    window_end = SCORING_DATE + timedelta(days=HORIZON_DAYS)

    if window_end > AS_OF_DATE:
        raise ValueError("The outcome window is not fully observed.")

    rng = random.Random(RANDOM_SEED)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        employees = connection.execute(
            """
            SELECT employee_id, employment_start_date
            FROM Employee
            WHERE employment_start_date <= ?
            ORDER BY employee_id
            """,
            (SCORING_DATE.isoformat(),),
        ).fetchall()

        if not employees:
            raise ValueError("No eligible employees were found.")

        # Only use information available by the scoring date.
        engagement_rows = connection.execute(
            """
            SELECT employee_id, engagement_score
            FROM EngagementSurvey
            WHERE survey_date <= ?
              AND response_status = 'Completed'
              AND engagement_score IS NOT NULL
            ORDER BY employee_id, survey_date DESC
            """,
            (SCORING_DATE.isoformat(),),
        ).fetchall()

        workload_rows = connection.execute(
            """
            SELECT employee_id, workload_hours_per_week,
                   workload_pressure_score
            FROM WorkloadSnapshot
            WHERE period_end <= ?
            ORDER BY employee_id, period_end DESC, period_start DESC
            """,
            (SCORING_DATE.isoformat(),),
        ).fetchall()

        promotion_rows = connection.execute(
            """
            SELECT employee_id, COUNT(*)
            FROM PromotionHistory
            WHERE event_date <= ?
            GROUP BY employee_id
            """,
            (SCORING_DATE.isoformat(),),
        ).fetchall()

        # Keep only the most recent eligible engagement/workload record.
        engagement = {}
        for employee_id, score in engagement_rows:
            engagement.setdefault(employee_id, score)

        workload = {}
        for employee_id, hours, pressure in workload_rows:
            workload.setdefault(employee_id, (hours, pressure))

        promotions = dict(promotion_rows)

        candidates = []

        for employee_id, start_text in employees:
            start_date = date.fromisoformat(start_text)
            tenure_days = (SCORING_DATE - start_date).days

            engagement_score = engagement.get(employee_id)
            hours, pressure = workload.get(employee_id, (None, None))
            promotion_count = promotions.get(employee_id, 0)

            # Neutral defaults are used when historical measurements
            # are unavailable; they do not use future records.
            engagement_score = (
                float(engagement_score)
                if engagement_score is not None else 3.0
            )
            hours = float(hours) if hours is not None else 42.0
            pressure = float(pressure) if pressure is not None else 50.0

            # Synthetic risk formula for demonstration purposes only.
            # Lower engagement and higher workload raise risk.
            risk_score = (
                (3.0 - engagement_score) * 1.2
                + ((pressure - 50.0) / 25.0) * 0.8
                + ((hours - 42.0) / 10.0) * 0.4
                - min(promotion_count, 3) * 0.15
                - min(tenure_days / 365.0, 10.0) * 0.05
                + rng.uniform(-0.35, 0.35)
            )

            candidates.append((employee_id, risk_score))

        # Select approximately the target proportion of employees
        # with the highest synthetic risk scores.
        candidates.sort(key=lambda item: (-item[1], item[0]))
        attrition_count = max(
            1, round(len(candidates) * VOLUNTARY_ATTRITION_RATE)
        )
        attrition_ids = {
            employee_id
            for employee_id, _ in candidates[:attrition_count]
        }

        # This version is deliberately separate from the old v1 labels.
        # Remove only previous v2 outcomes if this script is rerun.
        with connection:
            connection.execute(
                """
                DELETE FROM AttritionOutcome
                WHERE scoring_date = ?
                  AND horizon_days = ?
                  AND label_version = ?
                """,
                (
                    SCORING_DATE.isoformat(),
                    HORIZON_DAYS,
                    LABEL_VERSION,
                ),
            )

            inserted = 0

            for employee_id, _ in candidates:
                if employee_id in attrition_ids:
                    rng_days = random.Random(
                        f"{RANDOM_SEED}:{employee_id}:date"
                    )
                    offset = rng_days.randint(1, HORIZON_DAYS)
                    termination_date = (
                        SCORING_DATE + timedelta(days=offset)
                    )
                    status = "ObservedAttrition"
                    termination_type = "Voluntary"
                    label = 1
                    censoring_reason = None
                else:
                    termination_date = None
                    status = "ObservedNoAttrition"
                    termination_type = None
                    label = 0
                    censoring_reason = None

                connection.execute(
                    """
                    INSERT INTO AttritionOutcome (
                        outcome_id, employee_id, scoring_date,
                        horizon_days, outcome_window_end, outcome_status,
                        termination_date, termination_type,
                        label_voluntary_attrition, censoring_reason,
                        label_version, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        stable_id(
                            "OUTCOME",
                            employee_id,
                            SCORING_DATE.isoformat(),
                            HORIZON_DAYS,
                            LABEL_VERSION,
                        ),
                        employee_id,
                        SCORING_DATE.isoformat(),
                        HORIZON_DAYS,
                        window_end.isoformat(),
                        status,
                        termination_date.isoformat()
                        if termination_date else None,
                        termination_type,
                        label,
                        censoring_reason,
                        LABEL_VERSION,
                        AS_OF_DATE.isoformat(),
                    ),
                )
                inserted += 1

        print("Synthetic outcome generation completed.")
        print(f"Scoring date: {SCORING_DATE}")
        print(f"Outcome window end: {window_end}")
        print(f"Eligible employees: {len(candidates):,}")
        print(f"New v2 outcomes inserted: {inserted:,}")
        print(f"Synthetic attrition cases: {attrition_count:,}")
        print(
            "Synthetic attrition rate: "
            f"{attrition_count / len(candidates):.2%}"
        )
        print(
            "Integrity:",
            connection.execute("PRAGMA integrity_check").fetchone()[0],
        )
        print(
            "Foreign-key violations:",
            connection.execute("PRAGMA foreign_key_check").fetchall(),
        )


if __name__ == "__main__":
    generate_outcomes()