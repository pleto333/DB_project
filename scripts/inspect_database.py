from __future__ import annotations

import json
import os
from decimal import Decimal
from typing import Any

import mysql.connector


DB_NAME = os.getenv("DB_NAME", "stock_prediction_db")


def get_connection() -> mysql.connector.MySQLConnection:
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3307")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=DB_NAME,
        charset="utf8mb4",
        use_unicode=True,
    )


def json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return value


def print_section(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def print_rows(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        safe_row = {key: json_safe(value) for key, value in row.items()}
        print(json.dumps(safe_row, ensure_ascii=False, default=str))


def fetch_all(cursor: mysql.connector.cursor.MySQLCursorDict, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor.execute(sql, params)
    return cursor.fetchall()


def main() -> None:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        print_section("1. 테이블 목록")
        tables = fetch_all(
            cursor,
            """
            SELECT table_name, table_rows
            FROM information_schema.tables
            WHERE table_schema = %s
            ORDER BY table_name
            """,
            (DB_NAME,),
        )
        print_rows(tables)

        print_section("2. 컬럼 구조")
        columns = fetch_all(
            cursor,
            """
            SELECT
                table_name,
                column_name,
                column_type,
                is_nullable,
                column_key,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s
            ORDER BY table_name, ordinal_position
            """,
            (DB_NAME,),
        )
        print_rows(columns)

        print_section("3. 외래키 관계")
        relations = fetch_all(
            cursor,
            """
            SELECT
                table_name,
                column_name,
                referenced_table_name,
                referenced_column_name,
                constraint_name
            FROM information_schema.key_column_usage
            WHERE table_schema = %s
              AND referenced_table_name IS NOT NULL
            ORDER BY table_name, column_name
            """,
            (DB_NAME,),
        )
        print_rows(relations)

        print_section("4. 최신 추천 결과")
        recommendations = fetch_all(
            cursor,
            """
            SELECT
                a.analysis_id,
                r.rank_no,
                s.stock_code,
                s.stock_name,
                r.recommendation,
                r.reason,
                r.confidence
            FROM llm_analysis a
            JOIN stock_recommendations r ON r.analysis_id = a.analysis_id
            JOIN stocks s ON s.stock_id = r.stock_id
            ORDER BY a.analyzed_at DESC, r.rank_no
            LIMIT 10
            """,
        )
        print_rows(recommendations)

        print_section("5. 추천 근거 뉴스")
        news_articles = fetch_all(
            cursor,
            """
            SELECT
                a.analysis_id,
                n.article_id,
                n.title,
                n.publisher,
                n.published_at,
                n.url
            FROM llm_analysis a
            JOIN analysis_news_articles ana ON ana.analysis_id = a.analysis_id
            JOIN news_articles n ON n.article_id = ana.article_id
            ORDER BY a.analyzed_at DESC, n.published_at DESC
            LIMIT 10
            """,
        )
        print_rows(news_articles)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
