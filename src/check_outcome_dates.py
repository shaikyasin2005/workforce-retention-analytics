import sqlite3

connection = sqlite3.connect("data/workforce_retention.db")
cursor = connection.cursor()

print("ATTRITION OUTCOME DATES")

query = """
SELECT
    scoring_date,
    outcome_window_end,
    COUNT(*) AS total
FROM AttritionOutcome
GROUP BY scoring_date, outcome_window_end;
"""

for row in cursor.execute(query):
    print(row)

print("\nTENURE SNAPSHOT DATE RANGE")

query = """
SELECT
    MIN(snapshot_date),
    MAX(snapshot_date),
    COUNT(DISTINCT snapshot_date)
FROM TenureSnapshot;
"""

print(cursor.execute(query).fetchone())

connection.close()