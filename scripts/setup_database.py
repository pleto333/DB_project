from __future__ import annotations

import os
from pathlib import Path

import mysql.connector


ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_SQL = ROOT_DIR / "sql" / "schema.sql"
SAMPLE_DATA_SQL = ROOT_DIR / "sql" / "sample_data.sql"


def get_admin_connection() -> mysql.connector.MySQLConnection:
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3307")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        charset="utf8mb4",
        use_unicode=True,
    )


def split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single_quote = False
    in_double_quote = False
    previous_char = ""

    for char in sql_text:
        if char == "'" and not in_double_quote and previous_char != "\\":
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote and previous_char != "\\":
            in_double_quote = not in_double_quote

        if char == ";" and not in_single_quote and not in_double_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)

        previous_char = char

    statement = "".join(current).strip()
    if statement:
        statements.append(statement)

    return statements


def run_sql_file(cursor: mysql.connector.cursor.MySQLCursor, path: Path) -> None:
    sql_text = path.read_text(encoding="utf-8")
    for statement in split_sql_statements(sql_text):
        cursor.execute(statement)


def main() -> None:
    conn = get_admin_connection()
    cursor = conn.cursor()
    try:
        run_sql_file(cursor, SCHEMA_SQL)
        run_sql_file(cursor, SAMPLE_DATA_SQL)
        conn.commit()
        print("Database setup completed.")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
