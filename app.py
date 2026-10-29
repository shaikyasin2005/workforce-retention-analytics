from pathlib import Path
from datetime import date
import json
import sqlite3

import joblib
import pandas as pd
import streamlit as st

from src.employee_service import get_reference_data, add_employee


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = PROJECT_ROOT / "data" / "model_dataset.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "retention_model.joblib"
REPORT_PATH = PROJECT_ROOT / "models" / "evaluation_report.json"
IMPORTANCE_PATH = PROJECT_ROOT / "models" / "feature_importance.csv"


st.set_page_config(
    page_title="Workforce Retention Analytics",
    page_icon="📊",
    layout="wide",
)


@st.cache_data
def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    dataframe = pd.read_csv(DATA_PATH)
    required_columns = {
        "employee_id",
        "scoring_date",
        "horizon_days",
        "target",
    }
    missing_columns = required_columns - set(dataframe.columns)
    if missing_columns:
        raise ValueError(
            f"Dataset is missing columns: {sorted(missing_columns)}"
        )

    dataframe["scoring_date"] = dataframe["scoring_date"].astype(str)
    dataframe["horizon_days"] = pd.to_numeric(
        dataframe["horizon_days"], errors="coerce"
    )
    return dataframe


@st.cache_resource
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}"
        )
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_report():
    if not REPORT_PATH.exists():
        return {}
    return json.loads(
        REPORT_PATH.read_text(encoding="utf-8")
    )


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("📊 Workforce Retention Analytics")

st.caption(
    "Explore workforce attrition patterns and "
    "model-generated risk scores."
)

st.warning(
    "Demonstration only: this project uses synthetic employee "
    "data and synthetic attrition labels. Risk scores are not "
    "validated predictions of real employee resignations."
)


# --------------------------------------------------
# ADD EMPLOYEE
# --------------------------------------------------

st.divider()
st.header("Add Employee")
st.caption(
    "Register an employee with a valid role, team, "
    "and optional compensation details."
)

try:
    roles, teams, bands = get_reference_data()

    if not roles or not teams:
        st.warning(
            "Add at least one role and one team to the reference tables "
            "before registering employees."
        )
    else:
        with st.form("add_employee_form", clear_on_submit=True):
            employment_start_date = st.date_input(
                "Employment start date",
                value=date.today(),
                max_value=date.today(),
            )

            selected_role = st.selectbox(
                "Role",
                options=roles,
                format_func=lambda item: item[1],
            )

            selected_team = st.selectbox(
                "Team",
                options=teams,
                format_func=lambda item: item[1],
            )

            band_options = [("NONE", "Not specified")] + bands
            selected_band = st.selectbox(
                "Compensation band (optional)",
                options=band_options,
                format_func=lambda item: item[1],
            )

            submitted = st.form_submit_button(
                "Add Employee",
                type="primary",
            )

        if submitted:
            try:
                new_employee_id = add_employee(
                    employment_start_date=employment_start_date.isoformat(),
                    role_id=selected_role[0],
                    team_id=selected_team[0],
                    compensation_band_id=(
                        None if selected_band[0] == "NONE" else selected_band[0]
                    ),
                )

                # Clear cached data so the Employee Registry refreshes
                st.cache_data.clear()

                st.success(
                    f"Employee registered successfully: {new_employee_id}"
                )
                st.info(
                    "The employee and initial history records have been saved. "
                    "Historical snapshots, survey data, and model eligibility "
                    "have not been generated automatically."
                )
            except (ValueError, sqlite3.Error) as error:
                st.error(f"Could not register employee: {error}")

except (sqlite3.Error, OSError, ValueError) as error:
    st.error(f"Could not load employee registration data: {error}")


# --------------------------------------------------
# LOAD DATA AND MODEL
# --------------------------------------------------

try:
    data = load_data()
    model = load_model()
    report = load_report()

except (FileNotFoundError, ValueError, OSError) as error:
    st.error(str(error))
    st.info(
        "Check that the dataset and trained model exist "
        "in the data and models folders."
    )
    st.stop()


required_columns = {
    "employee_id",
    "scoring_date",
    "horizon_days",
    "target",
    "engagement_score",
    "workload_pressure_score",
    "workload_hours_per_week",
    "workload_category",
}

missing = required_columns - set(data.columns)

if missing:
    st.error(
        f"Dataset is missing columns: {sorted(missing)}"
    )
    st.stop()


# --------------------------------------------------
# GENERATE MODEL RISK SCORES
# --------------------------------------------------

excluded_columns = {
    "employee_id",
    "scoring_date",
    "horizon_days",
    "target",
}

feature_columns = [
    column
    for column in data.columns
    if column not in excluded_columns
]

X = data[feature_columns]

data["predicted_risk"] = model.predict_proba(X)[:, 1]


def risk_category(score):
    if score < 0.10:
        return "Very Low"
    if score < 0.30:
        return "Low"
    if score < 0.50:
        return "Moderate"
    if score < 0.70:
        return "Elevated"
    if score < 0.90:
        return "High"
    return "Very High"


data["risk_category"] = data["predicted_risk"].apply(
    risk_category
)


# --------------------------------------------------
# DASHBOARD FILTERS
# --------------------------------------------------

st.sidebar.header("Dashboard Filters")

risk_options = [
    "Very Low",
    "Low",
    "Moderate",
    "Elevated",
    "High",
    "Very High",
]

selected_risks = st.sidebar.multiselect(
    "Risk categories",
    options=risk_options,
    default=risk_options,
)

# The CSV currently represents one label version (v2). It contains
# scoring_date and horizon_days, but does not contain label_version.
available_dates = sorted(data["scoring_date"].dropna().unique().tolist())
if not available_dates:
    st.error("No scoring dates are available in the model dataset.")
    st.stop()

default_date = (
    "2026-07-30" if "2026-07-30" in available_dates
    else available_dates[-1]
)
selected_date = st.sidebar.selectbox(
    "Scoring date",
    options=available_dates,
    index=available_dates.index(default_date),
)

available_horizons = sorted(
    data.loc[
        data["scoring_date"] == selected_date,
        "horizon_days",
    ].dropna().unique().tolist()
)
if not available_horizons:
    st.error("No prediction horizons are available for this scoring date.")
    st.stop()
selected_horizon = st.sidebar.selectbox(
    "Prediction horizon (days)",
    options=available_horizons,
    index=(available_horizons.index(90) if 90 in available_horizons else 0),
)
st.sidebar.caption(
    "The current model dataset uses label version v2. "
    "A label-version selector requires rebuilding the CSV with that column "
    "and verifying a compatible trained model."
)

filtered = data[
    (data["scoring_date"] == selected_date)
    & (data["horizon_days"] == selected_horizon)
    & data["risk_category"].isin(selected_risks)
].copy()


# --------------------------------------------------
# KEY METRICS
# --------------------------------------------------

total = len(filtered)

high_risk = filtered["predicted_risk"].ge(0.70).sum()

average_risk = (
    filtered["predicted_risk"].mean()
    if total
    else 0
)

attrition_rate = (
    filtered["target"].mean()
    if total
    else 0
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Employees", f"{total:,}")
col2.metric("High-risk employees", f"{high_risk:,}")
col3.metric(
    "Average predicted risk",
    f"{average_risk:.1%}",
)
col4.metric(
    "Synthetic attrition rate",
    f"{attrition_rate:.1%}",
)


# --------------------------------------------------
# DASHBOARD CHARTS
# --------------------------------------------------

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Employee risk distribution")

    risk_counts = (
        filtered["risk_category"]
        .value_counts()
        .reindex(risk_options, fill_value=0)
    )

    st.bar_chart(risk_counts)

with right:
    st.subheader("Average engagement by outcome")

    engagement_summary = (
        filtered.groupby("target")["engagement_score"]
        .mean()
        .rename(
            index={
                0: "No attrition (synthetic)",
                1: "Attrition (synthetic)",
            }
        )
        .dropna()
    )

    st.bar_chart(engagement_summary)


# --------------------------------------------------
# FEATURE IMPORTANCE
# --------------------------------------------------

st.divider()
st.subheader("What factors influence attrition predictions?")

if IMPORTANCE_PATH.exists():
    importance_data = pd.read_csv(IMPORTANCE_PATH)

    if {"feature", "importance"}.issubset(importance_data.columns):
        importance_data = importance_data.sort_values(
            "importance",
            ascending=False,
        ).head(15).copy()

        importance_data["feature"] = (
            importance_data["feature"]
            .str.replace("numeric__", "", regex=False)
            .str.replace("categorical__", "", regex=False)
        )

        st.caption(
            "These scores show the relative importance of features "
            "to the Random Forest model overall. They do not prove "
            "that a feature causes an employee to leave."
        )

        st.bar_chart(
            importance_data.set_index("feature")["importance"],
            horizontal=True,
        )
    else:
        st.warning(
            "The feature-importance file has an unexpected format."
        )
else:
    st.info(
        "Feature importance has not been generated. "
        "Run: python src/feature_importance.py"
    )


# --------------------------------------------------
# MODEL EVALUATION
# --------------------------------------------------

st.subheader("Model evaluation")

if report:
    classification = report.get("classification_report", {})
    attrition_metrics = classification.get("Attrition", {})

    # Main evaluation metrics
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "ROC-AUC",
        f"{report.get('roc_auc', 0):.4f}",
    )

    col2.metric(
        "Accuracy",
        f"{classification.get('accuracy', 0):.1%}",
    )

    col3.metric(
        "Attrition precision",
        f"{attrition_metrics.get('precision', 0):.1%}",
    )

    col4.metric(
        "Attrition recall",
        f"{attrition_metrics.get('recall', 0):.1%}",
    )

    col5, col6, col7 = st.columns(3)

    col5.metric(
        "Attrition F1-score",
        f"{attrition_metrics.get('f1-score', 0):.1%}",
    )

    col6.metric(
        "Training rows",
        f"{report.get('training_rows', 0):,}",
    )

    col7.metric(
        "Testing rows",
        f"{report.get('testing_rows', 0):,}",
    )

    st.markdown("### Classification report")

    report_rows = []

    for class_name in ["No attrition", "Attrition", "macro avg", "weighted avg"]:
        metrics = classification.get(class_name)

        if metrics:
            report_rows.append({
                "Class": class_name,
                "Precision": metrics.get("precision", 0),
                "Recall": metrics.get("recall", 0),
                "F1-score": metrics.get("f1-score", 0),
                "Support": int(metrics.get("support", 0)),
            })

    if report_rows:
        report_table = pd.DataFrame(report_rows)

        st.dataframe(
            report_table.style.format({
                "Precision": "{:.1%}",
                "Recall": "{:.1%}",
                "F1-score": "{:.1%}",
                "Support": "{:,}",
            }),
            width="stretch",
            hide_index=True,
        )

    st.markdown("### Confusion matrix")

    matrix = report.get("confusion_matrix")

    if matrix and len(matrix) == 2 and all(len(row) == 2 for row in matrix):
        matrix_df = pd.DataFrame(
            matrix,
            index=["Actual: No attrition", "Actual: Attrition"],
            columns=["Predicted: No attrition", "Predicted: Attrition"],
        )

        st.dataframe(
            matrix_df,
            width="stretch",
        )

        st.caption(
            "Rows represent actual classes; columns represent "
            "predicted classes. The diagonal contains correct "
            "predictions, and the off-diagonal cells contain errors."
        )
    else:
        st.info("The confusion matrix is unavailable in the evaluation report.")

    st.caption(
        report.get(
            "note",
            "Evaluation results depend on the data used to train and test the model.",
        )
    )

else:
    st.info(
        "No evaluation report was found. Run "
        "python src/train_model.py to generate it."
    )



# --------------------------------------------------
# EMPLOYEE RISK RECORDS
# --------------------------------------------------

st.subheader("Employee risk records")

search = st.text_input(
    "Search by employee ID"
)

if search:
    filtered = filtered[
        filtered["employee_id"].str.contains(
            search,
            case=False,
            na=False,
        )
    ].copy()


display_columns = [
    "employee_id",
    "engagement_score",
    "workload_pressure_score",
    "workload_hours_per_week",
    "predicted_risk",
    "risk_category",
    "target",
]

display_data = (
    filtered[display_columns]
    .sort_values(
        "predicted_risk",
        ascending=False,
    )
)

st.dataframe(
    display_data.style.format(
        {
            "engagement_score": "{:.2f}",
            "workload_pressure_score": "{:.2f}",
            "workload_hours_per_week": "{:.2f}",
            "predicted_risk": "{:.1%}",
        }
    ),
    width="stretch",
    hide_index=True,
)

csv_data = display_data.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="📥 Download Employee Risk Records (CSV)",
    data=csv_data,
    file_name="employee_risk_records.csv",
    mime="text/csv",
)


# --------------------------------------------------
# EMPLOYEE RISK PROFILE
# --------------------------------------------------

st.divider()

st.subheader("Employee Risk Profile")

if not filtered.empty:

    employee_ids = sorted(
        filtered["employee_id"].unique()
    )

    selected_employee = st.selectbox(
        "Select an employee",
        options=employee_ids,
        key="employee_risk_profile",
    )

    employee = filtered[
        filtered["employee_id"] == selected_employee
    ].iloc[0]

    # ----------------------------------------------
    # EMPLOYEE METRICS
    # ----------------------------------------------

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Predicted risk",
        f"{employee['predicted_risk']:.1%}",
    )

    col2.metric(
        "Engagement score",
        (
            f"{employee['engagement_score']:.2f}"
            if pd.notna(employee["engagement_score"])
            else "Not available"
        ),
    )

    col3.metric(
        "Risk category",
        employee["risk_category"],
    )

    col4, col5 = st.columns(2)

    col4.metric(
        "Workload pressure",
        (
            f"{employee['workload_pressure_score']:.1f}"
            if pd.notna(
                employee["workload_pressure_score"]
            )
            else "Not available"
        ),
    )

    col5.metric(
        "Weekly workload hours",
        (
            f"{employee['workload_hours_per_week']:.1f}"
            if pd.notna(
                employee["workload_hours_per_week"]
            )
            else "Not available"
        ),
    )

    # ----------------------------------------------
    # SUGGESTED RETENTION ACTIONS
    # ----------------------------------------------

    st.markdown("**Suggested retention actions**")

    engagement = employee["engagement_score"]
    pressure = employee["workload_pressure_score"]
    hours = employee["workload_hours_per_week"]

    if pd.notna(engagement) and engagement < 2.5:
        st.write(
            "- Consider a supportive engagement conversation."
        )
    else:
        st.write(
            "- Continue regular engagement check-ins."
        )

    if pd.notna(pressure) and pressure >= 70:
        st.write(
            "- Review workload, priorities, and available support."
        )
    else:
        st.write(
            "- Review workload regularly with the employee."
        )

    if pd.notna(hours) and hours > 45:
        st.write(
            "- Review working hours and workload distribution."
        )

    st.caption(
        "Demonstration suggestions only; do not use synthetic "
        "risk scores for employment decisions."
    )

    
# ------------------------------------------
# INDIVIDUAL EMPLOYEE RISK EXPLANATION
# ------------------------------------------

st.divider()
st.subheader("Why is this employee at risk?")

st.write(
    "The observations below use simple feature thresholds "
    "to help interpret the selected employee's profile."
)

if not filtered.empty:
    explanation_employee = filtered[
        filtered["employee_id"] == selected_employee
    ].iloc[0] if "selected_employee" in locals() else None

    if explanation_employee is not None:

        # Engagement explanation
        engagement = explanation_employee["engagement_score"]

        if pd.isna(engagement):
            st.info("Engagement: No score is available.")
        elif engagement < 2.5:
            st.warning(
                "Engagement: The score is low. "
                "Consider a supportive engagement conversation."
            )
        else:
            st.success(
                "Engagement: The score is relatively strong, "
                "which is an encouraging observation."
            )

        # Workload pressure explanation
        pressure = explanation_employee["workload_pressure_score"]

        if pd.isna(pressure):
            st.info("Workload pressure: No score is available.")
        elif pressure >= 70:
            st.warning(
                "Workload pressure: Consider reviewing workload, "
                "priorities, and available support."
            )
        else:
            st.info(
                "Workload pressure: Consider checking with the "
                "employee about workload and current priorities."
            )

        # Weekly working hours explanation
        hours = explanation_employee["workload_hours_per_week"]

        if pd.isna(hours):
            st.info("Working hours: No data is available.")
        elif hours > 45:
            st.warning(
                "Working hours: Weekly hours exceed the "
                "45-hour review threshold."
            )
        else:
            st.info(
                "Working hours: Weekly hours are at or below "
                "the 45-hour review threshold."
            )

        st.caption(
            "These are rule-based observations, not proof of why "
            "an employee may leave. They are not direct explanations "
            "of the model's internal calculations. All scores and "
            "outcomes are synthetic."
        )
else:
    st.info(
        "Select risk categories that include employees "
        "to view an explanation."
    )


# --------------------------------------------------
# EMPLOYEE REGISTRY
# --------------------------------------------------

st.divider()
st.header("Employee Registry")

st.caption(
    "All employees registered in the database, "
    "including employees not yet eligible for model scoring."
)

DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"



@st.cache_data(ttl=5)
def load_employee_registry():
    import sqlite3

    with sqlite3.connect(DATABASE_PATH) as connection:
        registry = pd.read_sql_query(
            """
            SELECT
                e.employee_id,
                e.employment_start_date,
                e.employment_status,
                r.role_name AS role,
                t.team_name AS team,
                (
                    SELECT COUNT(*)
                    FROM TenureSnapshot ts
                    WHERE ts.employee_id = e.employee_id
                ) AS tenure_snapshots,
                (
                    SELECT COUNT(*)
                    FROM EngagementSurvey es
                    WHERE es.employee_id = e.employee_id
                ) AS engagement_surveys,
                (
                    SELECT COUNT(*)
                    FROM WorkloadSnapshot ws
                    WHERE ws.employee_id = e.employee_id
                ) AS workload_snapshots
            FROM Employee e
            LEFT JOIN Role r
                ON r.role_id = e.initial_role_id
            LEFT JOIN Team t
                ON t.team_id = e.initial_team_id
            ORDER BY e.employee_id
            """,
            connection,
        )

    dataset_path = PROJECT_ROOT / "data" / "model_dataset.csv"

    if dataset_path.exists():
        model_employee_ids = set(
            pd.read_csv(
                dataset_path,
                usecols=["employee_id"],
            )["employee_id"].astype(str)
        )
    else:
        model_employee_ids = set()

    registry["scoring_eligibility"] = registry["employee_id"].apply(
        lambda employee_id: (
            "In model dataset"
            if employee_id in model_employee_ids
            else "Not yet in model dataset"
        )
    )

    return registry

try:
    registry = load_employee_registry()

    st.metric("Registered employees", f"{len(registry):,}")

    registry_search = st.text_input(
        "Search registered employees by ID",
        key="registry_search",
    )

    if registry_search.strip():
        search_id = registry_search.strip().casefold()

        registry = registry[
            registry["employee_id"]
            .astype(str)
            .str.strip()
            .str.casefold()
            == search_id
        ]

        if registry.empty:
            st.warning(
                f"{registry_search.strip()} was not found in the "
                "registry results. The database record may exist, "
                "but the registry query needs checking."
            )

    st.dataframe(
        registry,
        width="stretch",
        hide_index=True,
    )

    st.download_button(
        label="📥 Download Employee Registry (CSV)",
        data=registry.to_csv(index=False).encode("utf-8"),
        file_name="employee_registry.csv",
        mime="text/csv",
    )

except Exception as error:
    st.error(f"Could not load employee registry: {error}")
