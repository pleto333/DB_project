from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import mysql.connector
from mysql.connector import Error


def get_connection() -> mysql.connector.MySQLConnection:
    """Create a MySQL connection."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "stock_prediction_db"),
        charset="utf8mb4",
        use_unicode=True,
    )


def _hash_url(url: str) -> str:
    """Make a fixed-length hash value to prevent duplicate news URLs."""
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()


def add_user(username: str, email: str, password_hash: str) -> int:
    """Add a login user."""
    sql = """
        INSERT INTO users (username, email, password_hash)
        VALUES (%s, %s, %s)
    """

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (username, email, password_hash))
        conn.commit()
        return cursor.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def add_stock(stock_code: str, stock_name: str, market: str = "KOSPI") -> int:
    """Add or update a stock."""
    sql = """
        INSERT INTO stocks (stock_code, stock_name, market)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            stock_id = LAST_INSERT_ID(stock_id),
            stock_name = VALUES(stock_name),
            market = VALUES(market)
    """

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (stock_code, stock_name, market))
        conn.commit()
        return cursor.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def save_news_article(
    title: str,
    url: str,
    summary: str | None = None,
    publisher: str | None = None,
    source: str = "ls_securities",
    published_at: str | None = None,
) -> int:
    """Save a news article collected from LS Securities API."""
    sql = """
        INSERT INTO news_articles
            (title, summary, url, url_hash, publisher, source, published_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            article_id = LAST_INSERT_ID(article_id),
            title = VALUES(title),
            summary = VALUES(summary),
            publisher = VALUES(publisher),
            source = VALUES(source),
            published_at = VALUES(published_at)
    """

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (title, summary, url, _hash_url(url), publisher, source, published_at))
        conn.commit()
        return cursor.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def save_llm_analysis(
    model_name: str,
    input_summary: str,
    response: dict[str, Any],
    user_id: int | None = None,
) -> int:
    """Save the original LLM API response."""
    sql = """
        INSERT INTO llm_analysis (user_id, model_name, input_summary, response_json)
        VALUES (%s, %s, %s, %s)
    """

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (user_id, model_name, input_summary, json.dumps(response, ensure_ascii=False)))
        conn.commit()
        return cursor.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def save_stock_recommendation(
    analysis_id: int,
    stock_id: int,
    rank_no: int,
    recommendation: str,
    reason: str,
    confidence: float | None = None,
) -> int:
    """Save one recommended stock from the LLM analysis result."""
    sql = """
        INSERT INTO stock_recommendations
            (analysis_id, stock_id, rank_no, recommendation, reason, confidence)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (analysis_id, stock_id, rank_no, recommendation, reason, confidence))
        conn.commit()
        return cursor.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_recommendations_json(analysis_id: int) -> dict[str, Any]:
    """Return recommendation data in the JSON format needed by UI."""
    sql = """
        SELECT
            r.rank_no,
            s.stock_code,
            s.stock_name,
            r.recommendation,
            r.reason,
            r.confidence
        FROM stock_recommendations r
        JOIN stocks s ON s.stock_id = r.stock_id
        WHERE r.analysis_id = %s
        ORDER BY r.rank_no
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, (analysis_id,))
        rows = cursor.fetchall()
        return {"recommendations": rows}
    finally:
        cursor.close()
        conn.close()


def get_latest_recommendations_json() -> dict[str, Any]:
    """Return the latest recommendation list."""
    sql = """
        SELECT analysis_id
        FROM llm_analysis
        ORDER BY analyzed_at DESC, analysis_id DESC
        LIMIT 1
    """

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        row = cursor.fetchone()
        if row is None:
            return {"recommendations": []}
        analysis_id = row[0]
    finally:
        cursor.close()
        conn.close()

    return get_recommendations_json(analysis_id)


if __name__ == "__main__":
    try:
        result = get_latest_recommendations_json()
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    except Error as exc:
        print(f"MySQL error: {exc}")
