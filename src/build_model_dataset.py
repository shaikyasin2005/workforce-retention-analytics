from pathlib import Path
import argparse
import sqlite3
from datetime import datetime

import pandas as pd


# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"
OUTPUT_PATH = PROJECT_ROOT / "data" / "model_dataset.csv"

SCORING_DATE = "2026-07-30"
HORIZON_DAYS = 90
LABEL_VERSION = "v2"


# --------------------------------------------------
# VALIDATION HELPERS
# --------------------------------------------------

def validate_scoring_date(value):
    """Validate that the date uses YYYY-MM-DD format."""
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as error:
        raise ValueError(
            "Invalid scoring date. Use YYYY-MM-DD, "
            "for example 2026-07-30."
        ) from error

    if parsed.isoformat() != value:
        raise ValueError(
            "Invalid scoring date. Use YYYY-MM-DD format."
        )

    return parsed


def validate_dataset(dataframe, scoring_date):
    """Validate labels, cohort eligibility and feature dates."""

    if dataframe.empty:
        raise ValueError("The generated dataset is empty.")

    # One row per employee for the selected scoring cohort.
    if dataframe["employee_id"].duplicated().any():
        duplicates = dataframe.loc[
            dataframe["employee_id"].duplicated(),
            "employee_id",
        ].tolist()

        raise ValueError(
            f"Duplicate employee records found: {duplicates[:10]}"
        )

    # Target must contain only binary labels.
    if not dataframe["target"].isin([0, 1]).all():
        raise ValueError("Target values must be 0 or 1.")

    # All rows must use the requested scoring date.
    dates = pd.to_datetime(
        dataframe["scoring_date"],
        errors="coerce",
    )

    if dates.isna().any():
        raise ValueError("Invalid scoring dates found.")

    if not (dates == pd.Timestamp(scoring_date)).all():
        raise ValueError(
            "Dataset contains unexpected scoring dates."
        )

    # All rows must use the requested horizon.
    if not (
        dataframe["horizon_days"] == HORIZON_DAYS
    ).all():
        raise ValueError(
            "Dataset contains unexpected prediction horizons."
        )

    # Employees must have started on or before scoring date.
    if (dataframe["tenure_days"] < 0).any():
        raise ValueError(
            "Negative tenure detected. "
            "An employee may have a future start date."
        )

    # Check dates of the actual historical records selected by SQL.
    source_date_columns = [
        "_tenure_source_date",
        "_survey_source_date",
        "_workload_source_date",
        "_assignment_effective_from",
        "_promotion_latest_event_date",
    ]

    for column in source_date_columns:
        if column not in dataframe.columns:
            continue

        source_dates = pd.to_datetime(
            dataframe[column],
            errors="coerce",
        )

        invalid_dates = (
            source_dates.notna()
            & (source_dates > pd.Timestamp(scoring_date))
        )

        if invalid_dates.any():
            bad_rows = dataframe.loc[
                invalid_dates,
                ["employee_id", column],
            ].head(10)

            raise ValueError(
                f"Future feature records detected in {column}:\n"
                f"{bad_rows.to_string(index=False)}"
            )

    # Verify assignment was active at the scoring date.
    if "_assignment_effective_to" in dataframe.columns:
        effective_to = pd.to_datetime(
            dataframe["_assignment_effective_to"],
            errors="coerce",
        )

        invalid_assignment = (
            effective_to.notna()
            & (effective_to < pd.Timestamp(scoring_date))
        )

        if invalid_assignment.any():
            raise ValueError(
                "An assignment that ended before the scoring "
                "date was selected."
            )

    print("Dataset validation passed.")
    print("Duplicate employees: 0")
    print("Invalid target values: 0")
    print("Unexpected scoring dates: 0")
    print("Invalid prediction horizons: 0")
    print("Future-dated selected features: 0")


# --------------------------------------------------
# DATASET GENERATION
# --------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Build a leakage-aware workforce retention "
            "dataset for a selected scoring date."
        )
    )

    parser.add_argument(
        "--scoring-date",
        default=SCORING_DATE,
        help="Scoring date in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--horizon-days",
        type=int,
        default=HORIZON_DAYS,
        help="Prediction horizon in days.",
    )

    parser.add_argument(
        "--label-version",
        default=LABEL_VERSION,
        help="Attrition outcome label version.",
    )

    parser.add_argument(
        "--output",
        default=str(OUTPUT_PATH),
        help="Output CSV path.",
    )

    args = parser.parse_args()

    scoring_date_obj = validate_scoring_date(
        args.scoring_date
    )
    scoring_date = scoring_date_obj.isoformat()

    if args.horizon_days <= 0:
        raise ValueError(
            "The prediction horizon must be greater than zero."
        )

    if not args.label_version.strip():
        raise ValueError("Label version cannot be empty.")

    output_path = Path(args.output)

    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    # --------------------------------------------------
    # SQL QUERY
    # --------------------------------------------------

    query = """
    WITH eligible_outcomes AS (
        SELECT
            employee_id,
            scoring_date,
            horizon_days,
            label_voluntary_attrition
        FROM AttritionOutcome
        WHERE scoring_date = ?
          AND horizon_days = ?
          AND label_version = ?
          AND outcome_status IN (
              'ObservedAttrition',
              'ObservedNoAttrition'
          )
          AND label_voluntary_attrition IN (0, 1)
    ),

    tenure_features AS (
        SELECT
            employee_id,
            snapshot_date,
            tenure_days,
            ROW_NUMBER() OVER (
                PARTITION BY employee_id
                ORDER BY snapshot_date DESC
            ) AS rn
        FROM TenureSnapshot
        WHERE date(snapshot_date) <= date(?)
    ),

    survey_features AS (
        SELECT
            employee_id,
            survey_date,
            engagement_score,
            response_status,
            ROW_NUMBER() OVER (
                PARTITION BY employee_id
                ORDER BY survey_date DESC, survey_id DESC
            ) AS rn
        FROM EngagementSurvey
        WHERE date(survey_date) <= date(?)
    ),

    workload_features AS (
        SELECT
            employee_id,
            period_start,
            period_end,
            workload_hours_per_week,
            workload_pressure_score,
            workload_category,
            ROW_NUMBER() OVER (
                PARTITION BY employee_id
                ORDER BY period_end DESC, period_start DESC
            ) AS rn
        FROM WorkloadSnapshot
        WHERE date(period_end) <= date(?)
    ),

    assignment_features AS (
        SELECT
            employee_id,
            role_id,
            team_id,
            effective_from,
            effective_to,
            ROW_NUMBER() OVER (
                PARTITION BY employee_id
                ORDER BY effective_from DESC, recorded_at DESC
            ) AS rn
        FROM EmployeeAssignmentHistory
        WHERE date(effective_from) <= date(?)
          AND (
              effective_to IS NULL
              OR date(effective_to) >= date(?)
          )
    ),

    promotion_features AS (
        SELECT
            employee_id,
            COUNT(*) AS promotion_event_count,
            MAX(event_date) AS latest_event_date
        FROM PromotionHistory
        WHERE date(event_date) <= date(?)
        GROUP BY employee_id
    )

    SELECT
        e.employee_id,
        o.scoring_date,
        o.horizon_days,

        CAST(
            julianday(o.scoring_date)
            - julianday(e.employment_start_date)
            AS INTEGER
        ) AS tenure_days,

        a.role_id,
        a.team_id,

        s.engagement_score,
        s.response_status AS survey_response_status,

        w.workload_hours_per_week,
        w.workload_pressure_score,
        w.workload_category,

        COALESCE(p.promotion_event_count, 0)
            AS promotion_event_count,

        o.label_voluntary_attrition AS target,

        -- Internal audit columns; removed before CSV export.
        t.snapshot_date AS _tenure_source_date,
        s.survey_date AS _survey_source_date,
        w.period_end AS _workload_source_date,
        a.effective_from AS _assignment_effective_from,
        a.effective_to AS _assignment_effective_to,
        p.latest_event_date AS _promotion_latest_event_date

    FROM eligible_outcomes o

    JOIN Employee e
        ON e.employee_id = o.employee_id

    LEFT JOIN tenure_features t
        ON t.employee_id = e.employee_id
       AND t.rn = 1

    LEFT JOIN survey_features s
        ON s.employee_id = e.employee_id
       AND s.rn = 1

    LEFT JOIN workload_features w
        ON w.employee_id = e.employee_id
       AND w.rn = 1

    LEFT JOIN assignment_features a
        ON a.employee_id = e.employee_id
       AND a.rn = 1

    LEFT JOIN promotion_features p
        ON p.employee_id = e.employee_id

    WHERE date(e.employment_start_date) <= date(o.scoring_date)

    ORDER BY e.employee_id;
    """

    # Eight feature cutoffs plus the three outcome filters.
    parameters = (
        scoring_date,
        args.horizon_days,
        args.label_version,
        scoring_date,  # tenure snapshots
        scoring_date,  # engagement surveys
        scoring_date,  # workload snapshots
        scoring_date,  # assignment effective_from
        scoring_date,  # assignment effective_to
        scoring_date,  # promotion events
    )

    # --------------------------------------------------
    # BUILD DATASET
    # --------------------------------------------------

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        dataframe = pd.read_sql_query(
            query,
            connection,
            params=parameters,
        )

    if dataframe.empty:
        print("No eligible records found.")
        print(f"Scoring date: {scoring_date}")
        print(f"Horizon: {args.horizon_days} days")
        print(f"Label version: {args.label_version}")
        print("No output file was written.")
        return

    # --------------------------------------------------
    # VALIDATE BEFORE EXPORT
    # --------------------------------------------------

    validate_dataset(dataframe, scoring_date)

    # Remove audit-only dates to preserve the original
    # 13-column model dataset and avoid training on metadata.
    audit_columns = [
        "_tenure_source_date",
        "_survey_source_date",
        "_workload_source_date",
        "_assignment_effective_from",
        "_assignment_effective_to",
        "_promotion_latest_event_date",
    ]

    dataframe = dataframe.drop(
        columns=audit_columns,
        errors="ignore",
    )

    expected_columns = [
        "employee_id",
        "scoring_date",
        "horizon_days",
        "tenure_days",
        "role_id",
        "team_id",
        "engagement_score",
        "survey_response_status",
        "workload_hours_per_week",
        "workload_pressure_score",
        "workload_category",
        "promotion_event_count",
        "target",
    ]

    dataframe = dataframe[expected_columns]

    # --------------------------------------------------
    # SAVE DATASET
    # --------------------------------------------------

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        output_path,
        index=False,
    )

    # --------------------------------------------------
    # REPORT
    # --------------------------------------------------

    attrition_cases = int(
        (dataframe["target"] == 1).sum()
    )

    no_attrition_cases = int(
        (dataframe["target"] == 0).sum()
    )

    print("\nMODEL DATASET CREATED")
    print("=" * 45)
    print(f"Scoring date: {scoring_date}")
    print(f"Horizon: {args.horizon_days} days")
    print(f"Label version: {args.label_version}")
    print(f"Rows: {len(dataframe):,}")
    print(f"Columns: {len(dataframe.columns)}")
    print(f"Attrition cases (target=1): {attrition_cases:,}")
    print(
        f"No-attrition cases (target=0): "
        f"{no_attrition_cases:,}"
    )
    print(f"Output: {output_path}")

    print("\nPreview:")
    print(dataframe.head())

    print("\nMissing values:")
    print(dataframe.isnull().sum())

    print("\nDataset generation completed successfully.")


if __name__ == "__main__":
    main()