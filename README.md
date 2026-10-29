# Workforce Retention Analytics

An end-to-end workforce retention analytics application that uses synthetic employee engagement, tenure, role, and workload signals to help prioritize supportive retention conversations. The solution combines a Streamlit dashboard, a SQLite data layer, machine-learning-based risk scoring, validation workflows, and ground-truth outcome exports.

> **Important:** This is a demonstration built with synthetic data. Its risk scores are not verified predictions of real employee behaviour and must not be used to make employment decisions.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Objectives](#objectives)
3. [Key Features](#key-features)
4. [Technology Stack](#technology-stack)
5. [Project Structure](#project-structure)
6. [Requirements](#requirements)
7. [Installation and Setup](#installation-and-setup)
8. [Running the Application](#running-the-application)
9. [Data and Ground Truth](#data-and-ground-truth)
10. [Machine Learning and Evaluation](#machine-learning-and-evaluation)
11. [Validation and Testing](#validation-and-testing)
12. [Important Scripts](#important-scripts)
13. [Reproducibility and Traceability](#reproducibility-and-traceability)
14. [Limitations and Responsible Use](#limitations-and-responsible-use)
15. [AI Assistance and Prompt History](#ai-assistance-and-prompt-history)
16. [Future Improvements](#future-improvements)

## Project Overview

Employee retention is influenced by several factors, including engagement, tenure, role, workload, and career development. This project demonstrates how synthetic workforce data can be processed to identify cases that may benefit from a supportive retention conversation.

The application brings together data management, feature preparation, risk scoring, outcome validation, and a dashboard for reviewing results. It is designed to make important decisions, exceptions, and validation results easier to inspect.

The system is a technical demonstration, not a replacement for employee conversations, professional judgement, or a properly validated workforce analytics process.

## Objectives

- Analyse synthetic engagement, tenure, role, and workload information.
- Produce retention-risk scores to help prioritize supportive conversations.
- Maintain traceability between source data, scoring dates, predictions, and outcome records.
- Validate outcome records and identify data-quality issues.
- Detect selected anomalies and potential feature leakage.
- Document model performance, assumptions, limitations, and verification steps.
- Provide a locally runnable Streamlit interface.

## Key Features

### Workforce retention dashboard

A Streamlit interface for viewing workforce retention analytics and reviewing the information exposed by the application.

### Data management

A SQLite database stores the project's structured data. Python modules provide database access and employee-related operations.

### Model dataset preparation

Dedicated scripts prepare model input data using scoring-date rules for relevant historical signals. Ground-truth outcome fields must remain separate from model input features.

### Risk scoring

A trained machine-learning model generates scores using the configured model pipeline. These scores are demonstration outputs and should not be interpreted as validated real-world probabilities.

### Ground-truth outcome exports

The repository includes CSV and JSON ground-truth exports for inspection and validation. These are separate from the model feature dataset.

### Validation and anomaly checks

The project includes scripts for checking dataset quality, outcome consistency, temporal conditions, potential feature leakage, and selected anomaly scenarios.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic, data preparation, and validation |
| Streamlit | Dashboard interface |
| SQLite | Structured local data storage |
| pandas | Tabular data processing |
| scikit-learn | Machine-learning workflows and evaluation |
| joblib | Model artifact serialization and loading |
| SQL | Database schema and data queries |
| Git and GitHub | Version control and source-code hosting |

## Project Structure

```text
workforce-retention-analytics/
├── app.py
├── README.md
├── ai_prompt_history.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── ground_truth.csv
│   └── ground_truth.json
├── docs/
│   ├── data_dictionary.md
│   └── source_manifest.json
├── sql/
│   └── schema.sql
└── src/
    ├── database.py
    ├── employee_service.py
    ├── build_model_dataset.py
    ├── generate_data.py
    ├── generate_dataset_v2.py
    ├── generate_new_employee_history.py
    ├── generate_outcomes.py
    ├── export_ground_truth.py
    ├── train_model.py
    ├── validate_dataset.py
    ├── check_feature_leakage.py
    ├── check_outcome_quality.py
    ├── check_v2_outcomes.py
    ├── test_anomaly_fixtures.py
    ├── test_model_robustness.py
    └── ...other analysis and verification scripts
```

### Repository artifact policy

The public repository includes source code, SQL, documentation, validation scripts, and ground-truth exports. The following local artifacts are intentionally excluded:

- The production SQLite database and database backups.
- Generated model input datasets.
- Serialized trained-model files.
- Local inspection reports and temporary test artifacts.

These exclusions keep the repository focused on source code and supporting documentation. A fresh clone will not automatically contain the excluded database, generated datasets, or trained model. Prepare them using the project's data-generation and model-building workflow before running any feature that depends on them.

The ground-truth exports contain synthetic demonstration records. Do not add real employee data, confidential information, credentials, or other sensitive information to the public repository.

## Requirements

- Python installed on your computer.
- Git, if you want to clone and version the project.
- Internet access to install Python dependencies.
- A local copy of the project.
- Local database and model artifacts for application features that require them.

The project dependencies are listed in `requirements.txt`.

## Installation and Setup

### 1. Clone the repository

Open PowerShell or a terminal:

```powershell
git clone https://github.com/shaikyasin2005/workforce-retention-analytics.git
cd workforce-retention-analytics
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents activation, you can use the Python executable inside the environment directly or follow Microsoft's guidance for your machine's execution policy. Do not change system security settings unnecessarily.

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Prepare local data and model artifacts

The production database, generated model datasets, and trained model binaries are not tracked in Git. Before using features that require them, follow the project's data-generation, dataset-building, and model-training scripts in `src/`.

Review each script before running it, particularly if it writes to an existing database or overwrites model artifacts. Use a separate test database when testing data-generation or registration workflows. Do not overwrite valuable local artifacts without making a backup.

The ground-truth exports already committed under `data/` are supporting outcome records; they do not replace the application's operational database or the model's input dataset.

## Running the Application

From the project root, with dependencies installed and required local artifacts prepared, run:

```powershell
python -m streamlit run app.py
```

Streamlit normally opens the application in your browser. If it does not, follow the local URL displayed in the terminal.

To stop the server, press `Ctrl+C` in the terminal running Streamlit.

**Verification:** The dashboard was launched successfully in the development environment. A clean clone still needs its excluded local artifacts prepared before all data-dependent features can be verified.

## Data and Ground Truth

The project separates model input data from ground-truth outcomes.

### Model input data

Model features are prepared from historical workforce signals according to the configured scoring date. Relevant source records should be limited to information available at or before that scoring date.

The dataset-building workflow includes temporal filters for signals such as surveys, workload periods, assignments, and promotion events. These filters are intended to reduce the risk of using information from the future.

### Ground-truth outcomes

The public ground-truth exports contain **19,110 outcome records** across two label versions:

- `data/ground_truth.csv`
- `data/ground_truth.json`

The exports include outcome identifiers, employee identifiers, scoring dates, prediction horizons, outcome statuses, label versions, validation information, and related metadata.

The current exports were checked and reported **zero validation issues** in their recorded validation fields. This is a result of the implemented checks, not a guarantee that every possible data-quality problem has been eliminated.

Some fields, such as a termination date for a record with no observed attrition, may be empty by design. Interpret missing values according to the data dictionary and outcome rules.

### Important separation rule

**Never use ground-truth outcomes, attrition labels, termination dates, or other information unavailable at scoring time as model input features.** Outcome data is intended for evaluation and traceability, not for leaking the answer into the prediction process.

See [`docs/data_dictionary.md`](docs/data_dictionary.md) for field definitions.

## Machine Learning and Evaluation

The project includes a model-training workflow and a model robustness check.

The development evaluation recorded the following results:

| Evaluation | Result |
|---|---:|
| ROC-AUC on the configured synthetic evaluation | 0.9755 |
| ROC-AUC with shuffled labels in a robustness check | 0.5146 |

ROC-AUC measures how well a model ranks positive cases above negative cases across classification thresholds. A value near 0.5 indicates performance close to random ranking for that test.

### How to interpret these results

The high ROC-AUC must be interpreted cautiously because the synthetic outcome labels were generated using rules related to risk features. This can create a strong relationship between input features and labels without demonstrating that the model will generalize to real employees.

The shuffled-label result is a useful sanity check, but it does not prove that the entire pipeline is free of leakage or that performance will transfer to another dataset.

Before any real-world use, evaluation would require independently collected and appropriately governed data, a leakage-resistant temporal holdout, calibration and threshold analysis, subgroup and fairness checks, and review by relevant domain experts.

## Validation and Testing

The project contains scripts for checking data integrity and selected system behaviours.

Run validation scripts only after preparing the local database and other artifacts required by each script. Check each script's source and dependencies first; some scripts inspect local database or model files that are not included in the public repository.

Examples of validation scripts include:

```powershell
python src/validate_dataset.py
python src/check_v2_outcomes.py
python src/test_anomaly_fixtures.py
python src/test_model_robustness.py
```

These are separate checks, and they may have different prerequisites. Do not interpret a command as passed unless it has actually completed successfully in your environment.

### Previously recorded development checks

The development checks completed for this project reported:

- SQLite integrity check: `ok`.
- Foreign-key violations: 0.
- Invalid outcome windows: 0.
- Duplicate outcome keys: 0.
- Isolated anomaly fixtures: 6 of 6 passed.
- Version 2 outcome consistency issues: 0.
- New-employee registration test completed using a temporary database without modifying the production database.

These results describe the checks run during development. Re-run relevant checks in the environment used for evaluation and record any differences.

## Important Scripts

| Script | Purpose |
|---|---|
| `src/database.py` | Database access utilities |
| `src/employee_service.py` | Employee-related operations |
| `src/generate_data.py` | Synthetic data generation |
| `src/build_model_dataset.py` | Model dataset preparation |
| `src/generate_dataset_v2.py` | Version 2 dataset workflow |
| `src/generate_outcomes.py` | Outcome generation |
| `src/export_ground_truth.py` | Ground-truth export |
| `src/train_model.py` | Model training |
| `src/validate_dataset.py` | Dataset validation |
| `src/check_feature_leakage.py` | Checks related to feature leakage |
| `src/check_outcome_quality.py` | Outcome quality checks |
| `src/check_v2_outcomes.py` | Version 2 outcome consistency checks |
| `src/test_anomaly_fixtures.py` | Isolated anomaly validation scenarios |
| `src/test_model_robustness.py` | Model robustness evaluation |

For exact arguments, configuration, and side effects, consult the relevant script. Do not assume that a script supports command-line flags unless they are implemented in its source.

## Reproducibility and Traceability

The project supports traceability through source code, SQL schema, data dictionary, ground-truth exports, and a source manifest.

- `sql/schema.sql` describes the database schema.
- `docs/data_dictionary.md` documents relevant fields.
- `docs/source_manifest.json` records checksums for the source files covered by the manifest.
- `ai_prompt_history.md` documents AI assistance and prompt history.
- Validation scripts provide repeatable checks for selected data-quality and model concerns.

For a reproducible run, record the Python version, installed dependency versions, dataset-generation settings, scoring date, label version, model configuration, and validation results.

The source manifest only verifies the files included in that manifest; it does not automatically verify excluded database and model artifacts.

## Limitations and Responsible Use

1. **Synthetic data:** The data does not represent a validated sample of a real workforce.
2. **Model generalization:** Synthetic evaluation results are not evidence of real-world predictive performance.
3. **Human oversight:** Risk scores should only support supportive, voluntary conversations—not disciplinary action, hiring, firing, promotion, or compensation decisions.
4. **Data leakage:** Features must be limited to information available at the scoring date. Outcome fields must remain separate from model inputs.
5. **Fairness and privacy:** Real-world deployment would require appropriate authorization, privacy controls, fairness evaluation, and domain review.
6. **Local artifacts:** The public repository excludes operational databases and model binaries. Data-dependent features require local preparation.
7. **Validation scope:** Passing the implemented checks does not establish that every possible error, security issue, or model weakness has been ruled out.

## AI Assistance and Prompt History

AI tools were used as part of the development and documentation workflow. The developer remains responsible for reviewing the implementation, understanding design choices, verifying results, and documenting limitations.

See [`ai_prompt_history.md`](ai_prompt_history.md) for the prompt history and the documented use of AI assistance. The history should reflect the prompts actually submitted and should distinguish verbatim prompts from summaries.

## Future Improvements

- Add a documented, repeatable setup workflow for generating local artifacts from a clean clone.
- Expand automated tests for database operations, application workflows, and edge cases.
- Add stronger temporal validation and independently held-out evaluation data.
- Evaluate model calibration, decision thresholds, and subgroup performance.
- Improve configuration management and application-level observability.
- Add explicit data-quality rules for missing and inconsistent outcome metadata.
- Improve the reproducibility of model training and evaluation reports.

## Repository

GitHub: https://github.com/shaikyasin2005/workforce-retention-analytics

This project is a demonstration of workforce analytics, data validation, and machine-learning workflows using synthetic data.
