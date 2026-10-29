from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "model_dataset.csv"


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "model_dataset.csv not found. "
            "Run python src/build_model_dataset.py first."
        )

    data = pd.read_csv(DATA_PATH)

    features = [
        "engagement_score",
        "workload_pressure_score",
        "workload_hours_per_week",
        "tenure_days",
        "promotion_event_count",
    ]

    print("ATTRITION FEATURE COMPARISON")
    print("=" * 60)

    print("\nAverage feature values by target:")
    print(
        data.groupby("target")[features]
        .mean()
        .round(2)
        .to_string()
    )

    print("\nNumber of employees in each group:")
    print(data["target"].value_counts().sort_index().to_string())

    print("\nCorrelation between numeric features and target:")
    print(
        data[features + ["target"]]
        .corr(numeric_only=True)["target"]
        .round(3)
        .to_string()
    )


if __name__ == "__main__":
    main()