from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "model_dataset.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "retention_model.joblib"


def main():
    data = pd.read_csv(DATA_PATH)
    model = joblib.load(MODEL_PATH)

    excluded = [
        "target",
        "employee_id",
        "scoring_date",
        "horizon_days",
    ]

    X = data.drop(columns=excluded)
    probabilities = model.predict_proba(X)[:, 1]

    results = pd.DataFrame({
        "employee_id": data["employee_id"],
        "actual_target": data["target"],
        "predicted_risk": probabilities,
    })

    print("RISK SCORE DISTRIBUTION")
    print("=" * 45)

    bins = [-0.001, 0.10, 0.30, 0.50, 0.70, 0.90, 1.001]
    labels = [
        "Very Low (0-10%)",
        "Low (10-30%)",
        "Moderate (30-50%)",
        "Elevated (50-70%)",
        "High (70-90%)",
        "Very High (90-100%)",
    ]

    results["risk_category"] = pd.cut(
        results["predicted_risk"],
        bins=bins,
        labels=labels,
        include_lowest=True,
    )

    print("\nEmployees in each risk category:")
    print(
        results["risk_category"]
        .value_counts(sort=False)
        .to_string()
    )

    print("\nRisk score statistics:")
    print(results["predicted_risk"].describe().round(4).to_string())

    print("\nAverage predicted risk by actual target:")
    print(
        results.groupby("actual_target")["predicted_risk"]
        .mean()
        .round(4)
        .to_string()
    )


if __name__ == "__main__":
    main()