import sqlite3
from pathlib import Path

database_path = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "workforce_retention.db"
)

connection = sqlite3.connect(database_path)

query = """
SELECT name
FROM sqlite_master
WHERE type = 'table'
ORDER BY name;
"""

tables = connection.execute(query).fetchall()

print("Database tables:")
for table in tables:
    print("-", table[0])

print("\nTotal tables:", len(tables))

connection.close()
