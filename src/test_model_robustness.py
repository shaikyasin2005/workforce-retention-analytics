from pathlib import Path

import joblib
import pandas as pd

from sklearn.base import clone
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "model_dataset.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "retention_model.joblib"

TARGET = "target"

DROP_COLUMNS = [
    "employee_id",
    "scoring_date",
    "horizon_days",
]

RANDOM_SEED = 20261022


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "Dataset not found. Run python src/build_model_dataset.py first."
        )

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Saved model not found. Run python src/train_model.py first."
        )

    data = pd.read_csv(DATA_PATH)

    X = data.drop(columns=[TARGET, *DROP_COLUMNS])
    y = data[TARGET].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_SEED,
        stratify=y,
    )

    # Evaluate the saved model on the same held-out split.
    saved_model = joblib.load(MODEL_PATH)
    original_probabilities = saved_model.predict_proba(X_test)[:, 1]
    original_auc = roc_auc_score(y_test, original_probabilities)

    # Shuffle only the training labels, leaving test labels untouched.
    shuffled_y_train = y_train.sample(
        frac=1,
        random_state=RANDOM_SEED,
    ).reset_index(drop=True)

    # Align shuffled labels to training rows.
    shuffled_y_train.index = y_train.index

    # Train a fresh copy of the saved pipeline.
    shuffled_model = clone(saved_model)
    shuffled_model.fit(X_train, shuffled_y_train)

    shuffled_probabilities = shuffled_model.predict_proba(X_test)[:, 1]
    shuffled_auc = roc_auc_score(y_test, shuffled_probabilities)

    print("MODEL ROBUSTNESS CHECK")
    print("=" * 40)
    print(f"Dataset rows: {len(data):,}")
    print(f"Training rows: {len(X_train):,}")
    print(f"Testing rows: {len(X_test):,}")
    print()
    print(f"Original-label test ROC-AUC: {original_auc:.4f}")
    print(f"Shuffled-label test ROC-AUC: {shuffled_auc:.4f}")
    print()
    print("INTERPRETATION")
    print(
        "The shuffled-label test is a diagnostic baseline, not proof "
        "of generalization to real employee data."
    )
    print(
        "A shuffled-label ROC-AUC near 0.50 is generally expected. "
        "A substantially different result needs investigation."
    )


if __name__ == "__main__":
    main()