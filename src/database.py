from pathlib import Path
import sqlite3

# Find the project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Database and SQL schema locations
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"


def initialize_database():
    """Create the SQLite database and initialize its tables."""

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"SQL schema not found: {SCHEMA_PATH}"
        )

    # Create the data folder if it doesn't exist
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Read the SQL schema
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    # Create the database tables
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema)

        # Check the database integrity
        integrity = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if integrity != "ok":
            raise RuntimeError(
                f"Database integrity check failed: {integrity}"
            )

    print("Database initialized successfully.")
    print(f"Database location: {DATABASE_PATH}")
    print(f"Integrity check: {integrity}")


if __name__ == "__main__":
    initialize_database()
