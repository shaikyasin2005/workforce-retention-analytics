import sqlite3
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
database_path = project_root / "data" / "workforce_retention_backup_before_10k.db"

connection = sqlite3.connect(database_path)

tables = connection.execute("""
    SELECT COUNT(*)
    FROM sqlite_master
    WHERE type = 'table'
      AND name NOT LIKE 'sqlite_%'
""").fetchone()[0]

employees = connection.execute(
    "SELECT COUNT(*) FROM Employee"
).fetchone()[0]

print("Tables:", tables)
print("Employees:", employees)

connection.close()