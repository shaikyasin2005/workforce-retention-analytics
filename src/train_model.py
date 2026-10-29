
from pathlib import Path
import argparse
import json

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "model_dataset.csv"
MODEL_DIR = PROJECT_ROOT / "models"

TARGET = "target"

DROP_COLUMNS = [
    "employee_id",
    "scoring_date",
    "horizon_days",
]

RANDOM_SEED = 20261022


# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Train and evaluate the workforce retention model."
    )

    parser.add_argument(
        "--data",
        default=str(DEFAULT_DATA_PATH),
        help="Path to the model dataset CSV.",
    )

    parser.add_argument(
        "--model-output",
        default="retention_model.joblib",
        help="Output model filename inside the models folder.",
    )

    parser.add_argument(
        "--report-output",
        default="evaluation_report.json",
        help="Output evaluation report filename inside the models folder.",
    )

    args = parser.parse_args()

    # Resolve the dataset path.
    data_path = Path(args.data)

    if not data_path.is_absolute():
        data_path = PROJECT_ROOT / data_path

    # Validate output filenames to prevent accidental path changes.
    if Path(args.model_output).name != args.model_output:
        raise ValueError("Model output must be a filename only.")

    if Path(args.report_output).name != args.report_output:
        raise ValueError("Report output must be a filename only.")

    if args.model_output == args.report_output:
        raise ValueError("Model and report filenames must be different.")

    # Check that the dataset exists.
    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {data_path}"
        )

    # Load the dataset.
    data = pd.read_csv(data_path)

    print("\nWORKFORCE RETENTION MODEL")
    print("=" * 50)
    print(f"Dataset: {data_path}")
    print(f"Dataset rows: {len(data):,}")

    # --------------------------------------------------
    # DATA VALIDATION
    # --------------------------------------------------

    required_columns = {TARGET, *DROP_COLUMNS}
    missing_columns = required_columns - set(data.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if data.empty:
        raise ValueError("The dataset is empty.")

    if data.columns.duplicated().any():
        raise ValueError("Duplicate column names detected.")

    if data["employee_id"].isna().any():
        raise ValueError("Employee IDs contain missing values.")

    if data["employee_id"].duplicated().any():
        raise ValueError("Duplicate employee IDs detected.")

    if data[TARGET].isna().any():
        raise ValueError("Target column contains missing values.")

    if not data[TARGET].isin([0, 1]).all():
        raise ValueError("Target values must be 0 or 1.")

    if data[TARGET].nunique() != 2:
        raise ValueError("Expected exactly two target classes.")

    if data["scoring_date"].isna().any():
        raise ValueError("Scoring dates contain missing values.")

    if data["horizon_days"].isna().any():
        raise ValueError("Prediction horizons contain missing values.")

    if (data["horizon_days"] <= 0).any():
        raise ValueError("Prediction horizons must be positive.")

    # --------------------------------------------------
    # PREPARE FEATURES AND TARGET
    # --------------------------------------------------

    # Identifiers and metadata must not be used as features.
    X = data.drop(columns=[TARGET, *DROP_COLUMNS])
    y = data[TARGET].astype(int)

    if X.shape[1] == 0:
        raise ValueError("No model features were found.")

    # Identify numeric and categorical columns.
    numeric_columns = X.select_dtypes(
        include=["number"]
    ).columns.tolist()

    categorical_columns = X.select_dtypes(
        exclude=["number"]
    ).columns.tolist()

    print(f"Features: {X.shape[1]}")
    print(f"Numeric features: {numeric_columns}")
    print(f"Categorical features: {categorical_columns}")

    print("\nTarget distribution:")
    print(y.value_counts().sort_index().rename({
        0: "No attrition",
        1: "Attrition",
    }))

    # --------------------------------------------------
    # PREPROCESSING
    # --------------------------------------------------

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="constant",
                    fill_value="Unknown",
                ),
            ),
            (
                "encoder",
                OneHotEncoder(handle_unknown="ignore"),
            ),
        ]
    )

    preprocessing = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                numeric_columns,
            ),
            (
                "categorical",
                categorical_pipeline,
                categorical_columns,
            ),
        ]
    )

    # --------------------------------------------------
    # MODEL
    # --------------------------------------------------

    model = Pipeline(
        steps=[
            (
                "preprocessing",
                preprocessing,
            ),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=200,
                    class_weight="balanced",
                    random_state=RANDOM_SEED,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    # --------------------------------------------------
    # TRAIN / TEST SPLIT
    # --------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_SEED,
        stratify=y,
    )

    print(f"\nTraining rows: {len(X_train):,}")
    print(f"Testing rows: {len(X_test):,}")

    # --------------------------------------------------
    # TRAIN MODEL
    # --------------------------------------------------

    print("\nTraining model...")

    model.fit(X_train, y_train)

    # --------------------------------------------------
    # EVALUATE MODEL
    # --------------------------------------------------

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    report = classification_report(
        y_test,
        predictions,
        labels=[0, 1],
        target_names=["No attrition", "Attrition"],
        output_dict=True,
        zero_division=0,
    )

    print("\nCLASSIFICATION REPORT")
    print(
        classification_report(
            y_test,
            predictions,
            labels=[0, 1],
            target_names=["No attrition", "Attrition"],
            zero_division=0,
        )
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=[0, 1],
    )

    print("CONFUSION MATRIX")
    print(matrix)

    auc = roc_auc_score(y_test, probabilities)
    print(f"\nROC-AUC: {auc:.4f}")

    # --------------------------------------------------
    # SAVE TO THE SELECTED OUTPUT FILES
    # --------------------------------------------------

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model_path = MODEL_DIR / args.model_output
    report_path = MODEL_DIR / args.report_output

    joblib.dump(model, model_path)

    evaluation = {
        "dataset_path": str(data_path),
        "dataset_rows": int(len(data)),
        "training_rows": int(len(X_train)),
        "testing_rows": int(len(X_test)),
        "target_counts": {
            str(key): int(value)
            for key, value in (
                y.value_counts().sort_index().items()
            )
        },
        "roc_auc": float(auc),
        "classification_report": report,
        "confusion_matrix": matrix.tolist(),
        "features": {
            "numeric": numeric_columns,
            "categorical": categorical_columns,
        },
        "random_seed": RANDOM_SEED,
        "note": (
            "Results are based on synthetic workforce data "
            "and synthetic attrition labels. They demonstrate "
            "the modelling pipeline, not validated real-world "
            "attrition prediction."
        ),
    }

    report_path.write_text(
        json.dumps(evaluation, indent=2),
        encoding="utf-8",
    )

    print("\nMODEL SAVED SUCCESSFULLY")
    print(f"Model: {model_path}")
    print(f"Evaluation report: {report_path}")
    print("\nExisting model files were not targeted unless")
    print("their filenames were explicitly selected.")


if __name__ == "__main__":
    main()