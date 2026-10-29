import sqlite3

connection = sqlite3.connect("data/workforce_retention.db")
cursor = connection.cursor()

print("HISTORY COVERAGE")

query = """
SELECT
    MIN(snapshot_date),
    MAX(snapshot_date),
    COUNT(DISTINCT substr(snapshot_date, 1, 7)),
    COUNT(DISTINCT snapshot_date)
FROM TenureSnapshot;
"""

print("Tenure:", cursor.execute(query).fetchone())

query = """
SELECT
    MIN(survey_date),
    MAX(survey_date),
    COUNT(DISTINCT substr(survey_date, 1, 7))
FROM EngagementSurvey;
"""

print("Surveys:", cursor.execute(query).fetchone())

query = """
SELECT
    MIN(period_start),
    MAX(period_end),
    COUNT(DISTINCT substr(period_start, 1, 7))
FROM WorkloadSnapshot;
"""

print("Workload:", cursor.execute(query).fetchone())

connection.close()