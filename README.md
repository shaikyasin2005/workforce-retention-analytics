# Workforce Retention Analytics

A Python-based workforce analytics project that explores employee engagement, tenure, workload, career progression, and synthetic attrition outcomes using SQLite, machine learning, and Streamlit.

## 1. Project Overview

Workforce Retention Analytics is a synthetic-data analytics project designed to study workforce patterns and demonstrate an end-to-end data analytics and machine learning workflow.

The system maintains relational employee records and longitudinal histories, builds time-aware model datasets, validates data quality, trains a classification model, and presents risk-related insights through an interactive Streamlit dashboard.

The dashboard includes employee registration, an Employee Registry, workforce analytics, risk categories, feature-importance analysis, model evaluation metrics, and downloadable CSV reports.

The project is intended for educational and demonstration purposes. Its synthetic predictions are not validated estimates of real employee resignations and must not be used as the sole basis for employment decisions.

## 2. Project Objectives

- Generate synthetic employee records and historical workforce data.
- Maintain relational integrity through primary keys, foreign keys, and database constraints.
- Analyze engagement, tenure, workload, roles, teams, compensation bands, and promotion history.
- Register employees and maintain initial assignment and compensation history.
- Build time-aware datasets for a defined scoring date and prediction horizon.
- Reduce temporal leakage by restricting historical features to information available on or before the scoring date.
- Train and evaluate a machine learning classification model.
- Examine feature importance and provide rule-based risk observations.
- Detect data-quality problems using validation and anomaly tests.
- Display workforce analytics through an interactive Streamlit dashboard.
- Preserve historical events and audit records rather than overwriting history.

## 3. Technology Stack

- **Language:** Python
- **Database:** SQLite
- **Data processing:** Pandas
- **Machine learning:** Scikit-learn
- **Model serialization:** Joblib
- **Dashboard:** Streamlit
- **Data storage:** CSV and JSON
- **Testing:** Python validation scripts and isolated anomaly fixtures
- **Version control:** Git and GitHub

Matplotlib or Plotly may be used where applicable, depending on the installed project code.

## 4. Project Structure

The following tree shows the main project components. It is illustrative rather than a complete inventory of every file in the repository.

```text
workforce-retention-analytics/
├── app.py
├── README.md
├── data/
│   ├── workforce_retention.db
│   ├── model_dataset.csv
│   ├── model_dataset_test.csv
│   └── ground_truth.csv
├── docs/
│   ├── data_dictionary.md
│   └── source_manifest.json
├── models/
│   ├── retention_model.joblib
│   ├── evaluation_report.json
│   └── feature_importance.csv
├── sql/
│   └── schema.sql
└── src/
    ├── database.py
    ├── employee_service.py
    ├── generate_data.py
    ├── generate_dataset_v2.py
    ├── generate_outcomes.py
    ├── generate_new_employee_history.py
    ├── build_model_dataset.py
    ├── train_model.py
    ├── feature_importance.py
    ├── validate_dataset.py
    ├── check_feature_leakage.py
    ├── check_scoring_cohort.py
    ├── check_v2_outcomes.py
    ├── test_anomaly_fixtures.py
    ├── test_model_robustness.py
    ├── verify_backup.py
    ├── verify_new_employee.py
    └── verify_registered_employee.py
```

Some generated files, scripts, and directories may differ between environments. Consult the actual repository for the current file inventory.

## 5. Main Data Entities

The relational database contains employee records and related workforce histories, including:

- `Employee`
- `Role`
- `Team`
- `TenureSnapshot`
- `EngagementSurvey`
- `WorkloadSnapshot`
- `CompensationBand`
- `EmployeeAssignmentHistory`
- `EmployeeCompensationHistory`
- `PromotionHistory`
- `AttritionOutcome`
- `AuditLog`

Refer to `sql/schema.sql` for database schema definitions and `docs/data_dictionary.md` for the documented data fields.

## 6. Installation and Setup

### Prerequisites

- Python installed on your system.
- A terminal such as PowerShell.
- VS Code or another Python editor.
- The project files and required data/model artifacts.

Use a Python version compatible with all installed project dependencies. Python 3.14 may work if compatible package versions are available.

### Clone the repository

If you are setting up the project from GitHub:

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd workforce-retention-analytics
```

Replace the placeholder with your actual repository URL.

If you already have the project locally, open the existing project directory instead.

### Create a virtual environment

From the project root:

```powershell
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the appropriate environment activation method for your system or run the environment's Python executable directly.

### Install dependencies

Install the core packages used by the application:

```powershell
python -m pip install pandas scikit-learn joblib streamlit
```

Install any additional dependencies imported by the scripts you intend to run.

For a reproducible setup, maintain a tested dependency file such as `requirements.txt` rather than relying on unpinned package versions.

## 7. Run the Streamlit Dashboard

From the project root:

```powershell
python -m streamlit run app.py
```

Open the local URL displayed in the terminal. Streamlit commonly uses `http://localhost:8501`, but the port may differ if it is already occupied.

The dashboard includes:

- Workforce retention analytics.
- Risk-category and scoring-date filters.
- Prediction horizon selection.
- Employee risk metrics and charts.
- Model evaluation results.
- Feature-importance visualization.
- Employee risk records and CSV downloads.
- An Add Employee form.
- An Employee Registry.

The dashboard requires the configured dataset, model, and other referenced files to be available.

## 8. Employee Registration and Registry

The dashboard provides an employee registration form backed by `src/employee_service.py`.

Users can:

- Select an employment start date.
- Choose an initial role.
- Choose an initial team.
- Select a compensation band when applicable.
- Register a new employee in the database.

The registration service creates the employee record and an initial assignment-history record. When a compensation band is supplied, it also creates the corresponding initial compensation-history record.

The registration operation uses a database transaction so the related inserts can be committed together or rolled back if an error occurs.

### Employee Registry

The Employee Registry displays employees registered in the database, including employees who are not eligible for the current historical model dataset.

It includes information such as:

- Employee ID.
- Employment start date and status.
- Role and team.
- Counts of tenure snapshots, engagement surveys, and workload snapshots.
- Whether the employee ID appears in the current model dataset.

The registry supports employee-ID searching and CSV export.

### Registration limitations

Registering an employee does not automatically generate tenure snapshots, engagement surveys, workload snapshots, attrition outcomes, or a model prediction.

An employee whose start date is after a historical scoring date should not be included in that historical scoring cohort.

The registration workflow was tested using an isolated temporary database copy. A separate read-only verification confirmed that `EMP-010003` had one assignment-history record and one compensation-history record. The isolated registration test did not modify the production database.

## 9. Build the Model Dataset

The project contains scripts for constructing a model dataset from workforce histories and attrition outcomes.

The current dataset configuration uses:

| Setting | Value |
|---|---|
| Scoring date | `2026-07-30` |
| Prediction horizon | 90 days |
| Label version | `v2` |
| Dataset rows | 9,555 |
| Attrition labels | 956 |
| No-attrition labels | 8,599 |

These values describe the current dataset and may change if the source data or generation parameters change.

A test build can be performed using the supported options of the dataset builder. For example, if the script exposes the following arguments:

```powershell
python src/build_model_dataset.py --scoring-date 2026-07-30 --output data/model_dataset_test.csv
```

Confirm the script's supported command-line arguments before running this example. Do not assume that every script version supports the same options.

**Important:** Build into a test output path first. Validate the resulting data before replacing the production dataset.

### Temporal considerations

The dataset builder is designed to select historical features available on or before the scoring date.

The existing date audit reported:

- 9,555 dataset rows.
- Zero rows dated after the expected scoring date.
- Zero rows with unexpected scoring dates.

These checks validate the dataset's scoring dates. They do not, by themselves, prove that every feature was derived from a valid historical source record. Source-record date validation is a separate requirement.

## 10. Train and Evaluate the Model

The project uses a Random Forest classifier with preprocessing for numeric and categorical features.

The training script is:

```powershell
python src/train_model.py
```

Before running it, verify the input dataset and output paths configured in the script.

Training may overwrite model artifacts or evaluation reports at the configured locations. Preserve backups and validate the intended dataset before retraining the production model.

The dashboard reads the configured model and evaluation-report artifacts to display risk scores and performance metrics.

## 11. Model Evaluation and Robustness Results

The current model robustness diagnostic reported the following results:

| Metric | Result |
|---|---:|
| Dataset rows | 9,555 |
| Training rows | 7,644 |
| Testing rows | 1,911 |
| Original-label test ROC-AUC | 0.9755 |
| Shuffled-label test ROC-AUC | 0.5146 |

The shuffled-label ROC-AUC is close to the random-ranking baseline of 0.50. This is a useful diagnostic for checking whether the evaluation process behaves as expected when labels are randomized.

However, the high original-label ROC-AUC must be interpreted cautiously.

The attrition labels in this project are synthetic and are generated using rules related to workforce risk factors. As a result, the model may learn relationships created by the label-generation process rather than generalizable patterns of real employee resignations.

These results describe performance on the project's synthetic dataset only. They are not evidence of equivalent performance on real workforce data.

## 12. Data Quality and Validation

The repository includes scripts for checking database consistency, scoring dates, outcome records, and selected anomaly conditions.

Run these commands from the project root when the corresponding scripts are present:

```powershell
python src/validate_dataset.py
python src/check_feature_leakage.py
python src/check_scoring_cohort.py
python src/check_v2_outcomes.py
python src/test_anomaly_fixtures.py
```

Additional verification utilities include:

```powershell
python src/verify_backup.py
python src/test_model_robustness.py
python src/verify_new_employee.py
python src/verify_registered_employee.py
```

These scripts serve different purposes. Review their output and source code to understand the scope of each check.

### Validation results observed during development

The database validation script reported:

| Validation | Result |
|---|---:|
| Employees | 10,003 |
| Tenure snapshots | 183,624 |
| Engagement surveys | 183,624 |
| Workload snapshots | 183,627 |
| Promotion events | 1,722 |
| Attrition outcomes | 19,110 |
| Invalid outcome date windows | 0 |
| Invalid observed attrition labels | 0 |
| Invalid observed no-attrition labels | 0 |
| Duplicate outcome keys | 0 |
| Database integrity | `ok` |
| Foreign-key violations | 0 |

The anomaly-fixture test reported that six isolated anomaly cases were detected:

- Missing survey.
- High workload.
- Invalid temporal window.
- Future-feature leakage.
- Invalid attrition label.
- Invalid recommendation records.

The test also reported that the main database was not modified.

These results describe the checks performed. They do not establish that every possible data-quality problem or leakage pathway has been eliminated.

## 13. Reproducibility

The project uses the configured random seed `20261022` in relevant synthetic-data and model-training workflows.

For more reproducible experiments:

- Record the exact script and command used to generate each artifact.
- Keep scoring date, prediction horizon, and label version fixed when comparing runs.
- Record package versions and the Python environment.
- Preserve the input dataset and relevant configuration.
- Validate output counts, labels, constraints, and date boundaries.
- Compare checksums when verifying deterministic outputs.

A fixed seed in one script does not guarantee that every project artifact is deterministic. Each generator and processing step should be tested independently.

## 14. Backup and Data Integrity

The project includes a backup-verification utility.

A successful backup check should be interpreted according to what the script actually verifies. Table counts and employee counts alone do not prove that a backup is a complete or current copy of the production database.

A robust backup procedure should preserve a consistent database copy, verify SQLite integrity and foreign-key constraints where appropriate, and compare relevant schema and record counts.

Keep backup files separate from production files, and avoid overwriting the only known-good backup during testing.

## 15. Synthetic Data and Model Limitations

All workforce records and attrition labels used by this project are synthetic.

Consequently:

- Synthetic labels do not establish real-world employee attrition behavior.
- High evaluation metrics may reflect the label-generation rules.
- Synthetic performance does not establish predictive accuracy on real employee data.
- Missing engagement surveys should not automatically be interpreted as negative engagement.
- High workload does not guarantee attrition.
- Feature importance does not establish causation.
- Rule-based observations are not direct explanations of the model's internal calculations.
- A historical dataset is not automatically suitable for predicting outcomes for newly registered employees.

Real-world use would require appropriate authorized data, rigorous temporal validation, privacy review, fairness assessment, calibration, monitoring, and independent evaluation.

## 16. Privacy and Responsible Use

The project is designed for educational and demonstration purposes.

Responsible-use principles include:

- Use synthetic or appropriately authorized data.
- Restrict access to employee-level records.
- Avoid sensitive personal attributes and inappropriate proxy variables.
- Explain the limitations of model outputs.
- Require human review before any intervention.
- Avoid using risk scores as the sole basis for employment decisions.
- Preserve intervention history and outcomes as explicit records where applicable.
- Apply appropriate access controls and retention policies before using real workforce information.

## 17. Documentation and Supporting Files

The repository may include:

- `docs/data_dictionary.md` — documented data fields and their meanings.
- `sql/schema.sql` — database tables, relationships, and constraints.
- `docs/source_manifest.json` — source-file manifest and checksums.
- Ground-truth exports — exported outcome records for inspection and validation.
- Evaluation reports — model metrics and related diagnostics.

A manifest or ground-truth export is useful for traceability, but neither independently proves that synthetic labels represent real-world outcomes.

## 18. Future Improvements

Potential improvements include:

- End-to-end reproducibility tests.
- Temporal evaluation across multiple scoring dates.
- More comprehensive source-record cutoff validation.
- Stronger separation between feature construction and outcome generation.
- A dedicated employee-history workflow for new registrations.
- Explicit intervention tracking and outcome analysis.
- Better automated test coverage for registration and dashboard workflows.
- Dependency pinning and environment documentation.
- Backup restoration tests.
- Improved dashboard accessibility and usability.
- Evaluation on appropriately authorized real-world data before any real-world predictive claims.

## 19. Project Status

The project currently includes:

- A relational SQLite database.
- Synthetic workforce histories and outcomes.
- Time-aware model-dataset construction.
- Data-quality validation utilities.
- An employee registration service and Employee Registry.
- A machine learning training and evaluation workflow.
- A Streamlit analytics dashboard.
- Feature-importance and risk-observation displays.
- Isolated anomaly tests and model robustness diagnostics.

The project demonstrates a complete educational workflow for workforce analytics, from relational data management through model evaluation and dashboard presentation. Its synthetic-data limitations remain central to interpreting the results responsibly.