from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "retention_model.joblib"


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Model not found. Run src/train_model.py first."
        )

    model = joblib.load(MODEL_PATH)

    preprocessing = model.named_steps["preprocessing"]
    classifier = model.named_steps["classifier"]

    feature_names = preprocessing.get_feature_names_out()
    importance = classifier.feature_importances_

    results = pd.DataFrame({
        "feature": feature_names,
        "importance": importance,
    })

    results = results.sort_values(
        "importance", ascending=False
    )

    print("TOP 15 FEATURE IMPORTANCES")
    print("=" * 45)
    print(results.head(15).to_string(index=False))

    output_path = (
        PROJECT_ROOT / "models" / "feature_importance.csv"
    )
    results.to_csv(output_path, index=False)

    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()