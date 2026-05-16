"""Utility script to inspect PostgreSQL databases and tables."""

import os
import sys

import psycopg2
from dotenv import load_dotenv

from src.config import PROJECT_ROOT, get_db_config

load_dotenv(PROJECT_ROOT / ".env")


def inspect_database(db_name: str) -> bool:
    cfg = get_db_config()
    try:
        print(f"\n=== Connecting to database: {db_name} ===")
        conn = psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            database=db_name,
            user=cfg["user"],
            password=cfg["password"],
        )
        print("Connected.")

        cur = conn.cursor()
        cur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        )
        tables = cur.fetchall()

        if not tables:
            print("No tables found.")
        else:
            for (table_name,) in tables:
                print(f"\n- Table: {table_name}")
                cur.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = %s
                    """,
                    (table_name,),
                )
                for col_name, col_type in cur.fetchall():
                    print(f"    {col_name}: {col_type}")

        cur.close()
        conn.close()
        return True
    except Exception as exc:
        print(f"Failed to connect to {db_name}: {exc}")
        return False


def main() -> None:
    primary = os.environ.get("DB_NAME", get_db_config()["database"])
    candidates = [primary, "paper_db", "academic", "research"]
    seen = set()
    success = False
    for db in candidates:
        if db in seen:
            continue
        seen.add(db)
        if inspect_database(db):
            success = True

    if not success:
        print("\nAll database connections failed. Check .env settings.")
        sys.exit(1)


if __name__ == "__main__":
    main()
