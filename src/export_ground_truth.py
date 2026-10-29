
from pathlib import Path
import csv
import json
import sqlite3
from datetime import date, datetime, timezone


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"
OUTPUT_JSON = PROJECT_ROOT / "data" / "ground_truth.json"
OUTPUT_CSV = PROJECT_ROOT / "data" / "ground_truth.csv"

# Optional filters. None means export every label version and scoring date.
SCORING_DATE_FILTER = None
LABEL_VERSION_FILTER = None

VALID_STATUSES = {
    "ObservedAttrition",
    "ObservedNoAttrition",
    "Censored",
    "Pending",
}


def validate_record(row, today):
    """Return validation issues for one outcome record."""
    issues = []

    scoring_date = date.fromisoformat(row["scoring_date"])
    window_end = date.fromisoformat(row["outcome_window_end"])

    if row["outcome_status"] not in VALID_STATUSES:
        issues.append("invalid_outcome_status")

    if row["horizon_days"] <= 0:
        issues.append("invalid_horizon")

    if window_end < scoring_date:
        issues.append("outcome_window_before_scoring_date")

    termination_text = row["termination_date"]
    termination_date = None

    if termination_text:
        try:
            termination_date = date.fromisoformat(termination_text)
        except ValueError:
            issues.append("invalid_termination_date")

    status = row["outcome_status"]
    label = row["label_voluntary_attrition"]
    termination_type = row["termination_type"]

    if status == "ObservedAttrition":
        if label != 1:
            issues.append("observed_attrition_label_not_1")
        if termination_date is None:
            issues.append("observed_attrition_missing_termination_date")
        if termination_type != "Voluntary":
            issues.append("observed_attrition_not_voluntary")
        if termination_date and not (
            scoring_date < termination_date <= window_end
        ):
            issues.append("termination_outside_outcome_window")

    elif status == "ObservedNoAttrition":
        if label != 0:
            issues.append("observed_no_attrition_label_not_0")
        if termination_date and (
            scoring_date < termination_date <= window_end
            and termination_type == "Voluntary"
        ):
            issues.append("no_attrition_label_conflicts_with_voluntary_termination")

    elif status == "Censored":
        if label is not None:
            issues.append("censored_record_has_label")

    # Pending and censored outcomes must not be treated as observed labels.
    if status in {"Pending", "Censored"} and label is not None:
        issues.append("unobserved_outcome_has_label")

    if window_end > today:
        expected_decision = "Outcome window has not ended; do not treat as a confirmed label."
    elif status == "ObservedAttrition" and label == 1:
        expected_decision = "Confirmed voluntary attrition within the outcome window."
    elif status == "ObservedNoAttrition" and label == 0:
        expected_decision = "Confirmed no voluntary attrition within the outcome window."
    elif status == "Censored":
        expected_decision = "Outcome is censored; exclude from supervised label training."
    elif status == "Pending":
        expected_decision = "Outcome is pending; exclude from supervised label training."
    else:
        expected_decision = "Review record because its status and label may be inconsistent."

    return issues, expected_decision


def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    today = date.today()
    filters = []
    parameters = []

    if SCORING_DATE_FILTER:
        filters.append("scoring_date = ?")
        parameters.append(SCORING_DATE_FILTER)

    if LABEL_VERSION_FILTER:
        filters.append("label_version = ?")
        parameters.append(LABEL_VERSION_FILTER)

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    query = f"""
        SELECT
            outcome_id,
            employee_id,
            scoring_date,
            horizon_days,
            outcome_window_end,
            outcome_status,
            termination_date,
            termination_type,
            label_voluntary_attrition,
            censoring_reason,
            label_version,
            created_at
        FROM AttritionOutcome
        {where_clause}
        ORDER BY scoring_date, employee_id, label_version
    """

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query, parameters).fetchall()

    ground_truth_records = []
    issue_count = 0

    for row in rows:
        record = dict(row)

        issues, expected_decision = validate_record(record, today)

        record["validation_issues"] = issues
        record["expected_decision"] = expected_decision
        record["requires_review"] = bool(issues)
        record["exported_at_utc"] = datetime.now(
            timezone.utc
        ).isoformat()

        issue_count += len(issues)
        ground_truth_records.append(record)

    summary = {
        "export_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_database": DATABASE_PATH.name,
        "record_count": len(ground_truth_records),
        "records_with_validation_issues": sum(
            1 for record in ground_truth_records
            if record["requires_review"]
        ),
        "validation_issue_count": issue_count,
        "filters": {
            "scoring_date": SCORING_DATE_FILTER,
            "label_version": LABEL_VERSION_FILTER,
        },
        "warning": (
            "Ground-truth and outcome fields must never be used as "
            "model input features."
        ),
        "records": ground_truth_records,
    }

    OUTPUT_JSON.write_text(
        json.dumps(summary, indent=2, default=str),
        encoding="utf-8",
    )

    csv_fields = [
        "outcome_id",
        "employee_id",
        "scoring_date",
        "horizon_days",
        "outcome_window_end",
        "outcome_status",
        "termination_date",
        "termination_type",
        "label_voluntary_attrition",
        "censoring_reason",
        "label_version",
        "validation_issues",
        "expected_decision",
        "requires_review",
    ]

    with OUTPUT_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=csv_fields)
        writer.writeheader()

        for record in ground_truth_records:
            output_record = {
                field: record.get(field)
                for field in csv_fields
            }
            output_record["validation_issues"] = json.dumps(
                record["validation_issues"]
            )
            writer.writerow(output_record)

    print("\nGROUND-TRUTH EXPORT COMPLETED")
    print("=" * 45)
    print(f"Records exported: {len(ground_truth_records):,}")
    print(f"Records needing review: {summary['records_with_validation_issues']:,}")
    print(f"Validation issues: {issue_count:,}")
    print(f"JSON: {OUTPUT_JSON}")
    print(f"CSV: {OUTPUT_CSV}")
    print("\nThese files are separate from the model dataset.")


if __name__ == "__main__":
    main()