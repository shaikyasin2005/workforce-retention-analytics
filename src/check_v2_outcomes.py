
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"


def main():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                employee_id,
                scoring_date,
                horizon_days,
                outcome_window_end,
                outcome_status,
                termination_date,
                termination_type,
                label_voluntary_attrition
            FROM AttritionOutcome
            WHERE scoring_date = ?
              AND horizon_days = ?
              AND label_version = ?
            """,
            ("2026-07-30", 90, "v2"),
        ).fetchall()

    problems = []

    for row in rows:
        status = row["outcome_status"]
        label = row["label_voluntary_attrition"]
        termination = row["termination_date"]
        termination_type = row["termination_type"]
        start = row["scoring_date"]
        end = row["outcome_window_end"]

        if status == "ObservedAttrition":
            if label != 1:
                problems.append(
                    (row["employee_id"], "Attrition label is not 1")
                )

            if termination_type != "Voluntary":
                problems.append(
                    (row["employee_id"], "Termination is not voluntary")
                )

            if not termination or not (start < termination <= end):
                problems.append(
                    (row["employee_id"], "Termination date outside window")
                )

        elif status == "ObservedNoAttrition":
            if label != 0:
                problems.append(
                    (row["employee_id"], "No-attrition label is not 0")
                )

            if termination is not None:
                problems.append(
                    (row["employee_id"], "Unexpected termination date")
                )

    print("V2 OUTCOME CONSISTENCY CHECK")
    print("=" * 40)
    print(f"Records checked: {len(rows):,}")
    print(f"Consistency issues: {len(problems):,}")

    for employee_id, issue in problems[:20]:
        print(f"{employee_id}: {issue}")

    if not problems:
        print("PASS: All checked outcome records are consistent.")
    else:
        print("FAIL: Review the issues above.")


if __name__ == "__main__":
    main()
