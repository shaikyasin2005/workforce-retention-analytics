from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"


def inspect_schema():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        tables = connection.execute("""
            SELECT name, sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        print(f"Database: {DATABASE_PATH}")
        print(f"Total tables: {len(tables)}")

        for table_name, create_sql in tables:
            print("\n" + "=" * 80)
            print(f"TABLE: {table_name}")
            print("=" * 80)

            print("\nCREATE STATEMENT:")
            print(create_sql)

            print("\nCOLUMNS:")
            for column in connection.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall():
                print(column)

            print("\nFOREIGN KEYS:")
            foreign_keys = connection.execute(
                f'PRAGMA foreign_key_list("{table_name}")'
            ).fetchall()

            if foreign_keys:
                for foreign_key in foreign_keys:
                    print(foreign_key)
            else:
                print("None")

            print("\nINDEXES:")
            indexes = connection.execute(
                f'PRAGMA index_list("{table_name}")'
            ).fetchall()

            if indexes:
                for index in indexes:
                    print(index)
            else:
                print("None")


if __name__ == "__main__":
    inspect_schema()