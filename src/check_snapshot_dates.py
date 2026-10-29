import sqlite3

connection = sqlite3.connect("data/workforce_retention.db")
cursor = connection.cursor()

query = """
SELECT
    substr(snapshot_date, 1, 7) AS snapshot_month,
    COUNT(DISTINCT snapshot_date) AS distinct_dates,
    COUNT(*) AS total_snapshots
FROM TenureSnapshot
GROUP BY substr(snapshot_date, 1, 7)
ORDER BY snapshot_month;
"""

print("MONTHLY TENURE SNAPSHOT SUMMARY")

for row in cursor.execute(query):
    print(row)

connection.close()