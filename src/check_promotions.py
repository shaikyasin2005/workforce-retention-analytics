import sqlite3

connection = sqlite3.connect("data/workforce_retention.db")
cursor = connection.cursor()

print("PROMOTION HISTORY CHECK")

query = """
SELECT
    COUNT(*) AS total_events,
    COUNT(DISTINCT employee_id) AS employees_promoted,
    MIN(event_date) AS first_event,
    MAX(event_date) AS last_event
FROM PromotionHistory;
"""

print(cursor.execute(query).fetchone())

print("\nPROMOTION EVENTS BY TYPE")

query = """
SELECT progression_type, COUNT(*)
FROM PromotionHistory
GROUP BY progression_type
ORDER BY progression_type;
"""

for row in cursor.execute(query):
    print(row)

print("\nDATABASE INTEGRITY")
print(cursor.execute("PRAGMA integrity_check").fetchone()[0])

connection.close()