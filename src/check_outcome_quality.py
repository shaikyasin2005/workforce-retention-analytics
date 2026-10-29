import sqlite3

connection = sqlite3.connect("data/workforce_retention.db")
cursor = connection.cursor()

print("OUTCOME QUALITY CHECK")

query = """
SELECT
    outcome_status,
    COUNT(*) AS total,
    ROUND(100.0 * COUNT(*) /
        (SELECT COUNT(*) FROM AttritionOutcome), 2) AS percentage
FROM AttritionOutcome
GROUP BY outcome_status
ORDER BY outcome_status;
"""

for row in cursor.execute(query):
    print(row)

print("\nVOLUNTARY ATTRITION RATE")

query = """
SELECT
    label_version,
    scoring_date,
    horizon_days,
    COUNT(*) AS total_outcomes,
    SUM(label_voluntary_attrition) AS voluntary_attritions,
    ROUND(
        100.0 * AVG(label_voluntary_attrition),
        2
    ) AS attrition_rate
FROM AttritionOutcome
WHERE label_version = 'v2'
  AND scoring_date = '2026-07-30'
  AND horizon_days = 90
  AND label_voluntary_attrition IS NOT NULL
GROUP BY label_version, scoring_date, horizon_days;
"""

print(cursor.execute(query).fetchone())

print("\nOUTCOME WINDOW CHECK")

query = """
SELECT
    MIN(scoring_date),
    MAX(scoring_date),
    MIN(outcome_window_end),
    MAX(outcome_window_end),
    MIN(horizon_days),
    MAX(horizon_days)
FROM AttritionOutcome;
"""

print(cursor.execute(query).fetchone())

connection.close()