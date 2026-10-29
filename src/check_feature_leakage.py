from pathlib import Path
import sqlite3
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"
DATASET_PATH = PROJECT_ROOT / "data" / "model_dataset.csv"
SCORING_DATE = "2026-07-30"

def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    print("FEATURE LEAKAGE AUDIT")
    print("=" * 45)
    print("Scoring date:", SCORING_DATE)

    checks = {
        "Tenure snapshots after scoring date": """
            SELECT COUNT(*) FROM TenureSnapshot
            WHERE snapshot_date > ?
        """,
        "Engagement surveys after scoring date": """
            SELECT COUNT(*) FROM EngagementSurvey
            WHERE survey_date > ?
        """,
        "Workload snapshots ending after scoring date": """
            SELECT COUNT(*) FROM WorkloadSnapshot
            WHERE period_end > ?
        """,
        "Promotion events after scoring date": """
            SELECT COUNT(*) FROM PromotionHistory
            WHERE event_date > ?
        """,
    }

    with sqlite3.connect(DATABASE_PATH) as connection:
        for description, query in checks.items():
            count = connection.execute(
                query, (SCORING_DATE,)
            ).fetchone()[0]
            print(f"{description}: {count:,}")

    print("\nMODEL DATASET CHECK")
    data = pd.read_csv(DATASET_PATH)

    if data.empty:
        raise ValueError("The model dataset is empty.")

    if "scoring_date" not in data.columns:
        raise ValueError("Dataset has no scoring_date column.")

    dates = pd.to_datetime(data["scoring_date"], errors="coerce")

    if dates.isna().any():
        raise ValueError("Invalid scoring dates found in dataset.")

    scoring_date = pd.Timestamp(SCORING_DATE)

    future_rows = int((dates > scoring_date).sum())
    mismatched_rows = int((dates != scoring_date).sum())

    print(f"Dataset rows: {len(data):,}")
    print(f"Rows dated after scoring date: {future_rows:,}")
    print(f"Rows with unexpected scoring dates: {mismatched_rows:,}")

    if future_rows or mismatched_rows:
        raise ValueError("Dataset scoring-date validation failed.")

    print("\nPASS: All dataset rows use the expected scoring date.")
    print(
        "Note: This validates dataset dates, not every feature's "
        "historical source record."
    )

if __name__ == "__main__":
    main()