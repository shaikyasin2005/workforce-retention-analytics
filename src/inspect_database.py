from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"

if not DATABASE_PATH.exists():
    raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

with sqlite3.connect(DATABASE_PATH) as connection:
    tables = connection.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """).fetchall()

    print(f"Database: {DATABASE_PATH}")
    print(f"Total tables: {len(tables)}")

    for (table_name,) in tables:
        columns = connection.execute(
            f'PRAGMA table_info("{table_name}")'
        ).fetchall()

        count = connection.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()[0]

        print(f"\nTABLE: {table_name}")
        print("COLUMNS:", ", ".join(column[1] for column in columns))
        print("ROWS:", count)