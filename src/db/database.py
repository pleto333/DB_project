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


def get_user_by_username(username: str) -> dict[str, Any] | None:
    """Return user row by username, or None if not found."""
    sql = "SELECT user_id, username, email, password_hash FROM users WHERE username = %s"

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, (username,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_latest_analysis_json() -> dict[str, Any]:
    """
    recommendations → stock_recommendations JOIN stocks 에서 조회.
    theme/news_evidence 등 정규화되지 않은 보조 필드는 llm_analysis.response_json 에서 보완.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # ① 최신 분석 메타데이터
        cursor.execute("""
            SELECT analysis_id, response_json, analyzed_at
            FROM llm_analysis
            ORDER BY analyzed_at DESC, analysis_id DESC
            LIMIT 1
        """)
        meta = cursor.fetchone()
        if meta is None:
            return {}

        analysis_id = meta["analysis_id"]
        analyzed_at = str(meta["analyzed_at"])
        response_json = meta.get("response_json") or {}
        if isinstance(response_json, str):
            response_json = json.loads(response_json)

        # ② stock_recommendations JOIN stocks — 정규화된 추천 종목 조회
        cursor.execute("""
            SELECT
                sr.rank_no,
                sr.recommendation,
                sr.reason,
                sr.confidence,
                s.stock_code,
                s.stock_name,
                s.market
            FROM stock_recommendations sr
            JOIN stocks s ON s.stock_id = sr.stock_id
            WHERE sr.analysis_id = %s
            ORDER BY sr.rank_no
        """, (analysis_id,))
        db_recs = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    # ③ response_json 추천 목록을 rank 기준 맵으로 준비 (보조 필드 보완용)
    json_rec_map = {
        r.get("rank"): r
        for r in (response_json.get("recommendations") or [])
    }

    merged_recs = []
    for row in db_recs:
        rank = row["rank_no"]
        conf = float(row["confidence"]) if row["confidence"] is not None else 0.5
        # DB에는 0.0~1.0 소수로 저장, 화면용 레이블로 역변환
        conf_label = "상" if conf >= 0.7 else ("하" if conf <= 0.3 else "중")
        sup = json_rec_map.get(rank, {})
        merged_recs.append({
            "rank":             rank,
            "stock_name":       row["stock_name"],       # stocks 테이블
            "stock_code":       row["stock_code"],       # stocks 테이블
            "market":           row["market"],           # stocks 테이블
            "recommendation":   row["recommendation"],   # stock_recommendations
            "reason":           row["reason"],           # stock_recommendations
            "confidence":       sup.get("confidence", conf_label),
            # response_json 보완 필드
            "theme":            sup.get("theme", ""),
            "news_evidence":    sup.get("news_evidence", ""),
            "expected_momentum": sup.get("expected_momentum", ""),
            "risk":             sup.get("risk", ""),
        })

    # DB에 추천 데이터가 없으면 response_json 그대로 사용 (구버전 호환)
    if not merged_recs:
        merged_recs = response_json.get("recommendations", [])

    return {
        "analysis_id":           analysis_id,
        "analyzed_at":           analyzed_at,
        "analysis_date":         response_json.get("analysis_date", ""),
        "top_themes":            response_json.get("top_themes", []),
        "market_news":           response_json.get("market_news", {}),
        "overall_market_summary": response_json.get("overall_market_summary", ""),
        "disclaimer":            response_json.get("disclaimer", ""),
        "recommendations":       merged_recs,
    }


def get_latest_news_articles(limit: int = 20) -> list[dict[str, Any]]:
    """news_articles 테이블에서 최근 수집된 뉴스 반환."""
    sql = """
        SELECT article_id, title, summary, publisher, source,
               published_at, collected_at
        FROM news_articles
        ORDER BY collected_at DESC
        LIMIT %s
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, (limit,))
        return [
            {
                "article_id":   r["article_id"],
                "title":        r["title"],
                "summary":      r["summary"] or "",
                "publisher":    r["publisher"] or "LS증권",
                "source":       r["source"],
                "published_at": str(r["published_at"]) if r["published_at"] else "",
                "collected_at": str(r["collected_at"]),
            }
            for r in cursor.fetchall()
        ]
    finally:
        cursor.close()
        conn.close()


def get_news_by_stock(stock_name: str, stock_code: str, limit: int = 5) -> list[dict[str, Any]]:
    """종목명 또는 종목코드가 포함된 news_articles 반환."""
    sql = """
        SELECT article_id, title, summary, publisher, published_at, collected_at
        FROM news_articles
        WHERE title LIKE %s OR summary LIKE %s
        ORDER BY collected_at DESC
        LIMIT %s
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 종목명으로 먼저 검색
        pattern = f"%{stock_name}%"
        cursor.execute(sql, (pattern, pattern, limit))
        rows = cursor.fetchall()
        # 결과 없으면 종목코드로 재검색
        if not rows and stock_code:
            code_pattern = f"%{stock_code}%"
            cursor.execute(sql, (code_pattern, code_pattern, limit))
            rows = cursor.fetchall()
        return [
            {
                "article_id": r["article_id"],
                "title": r["title"],
                "summary": r["summary"] or "",
                "publisher": r["publisher"] or "LS증권",
                "published_at": str(r["published_at"]) if r["published_at"] else "",
                "collected_at": str(r["collected_at"]),
            }
            for r in rows
        ]
    finally:
        cursor.close()
        conn.close()


def search_stocks(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """종목명 또는 종목코드로 stocks 테이블 검색."""
    sql = """
        SELECT stock_code, stock_name, market
        FROM stocks
        WHERE (stock_code LIKE %s OR stock_name LIKE %s)
          AND stock_code NOT LIKE 'TBD\\_%%'
        ORDER BY
            CASE
                WHEN stock_code = %s THEN 0
                WHEN stock_name = %s THEN 1
                ELSE 2
            END,
            LENGTH(stock_name),
            stock_name
        LIMIT %s
    """
    pattern = f"%{query}%"
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, (pattern, pattern, query, query, limit))
        return [
            {"stock_code": r["stock_code"], "stock_name": r["stock_name"], "market": r["market"]}
            for r in cursor.fetchall()
        ]
    finally:
        cursor.close()
        conn.close()


def add_portfolio_item(user_id: int, stock_code: str, stock_name: str) -> int:
    """Add a stock to user's portfolio. Ignores duplicates."""
    sql = """
        INSERT INTO portfolio (user_id, stock_code, stock_name)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE portfolio_id = LAST_INSERT_ID(portfolio_id)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (user_id, stock_code, stock_name))
        conn.commit()
        return cursor.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def remove_portfolio_item(user_id: int, stock_code: str) -> None:
    """Remove a stock from user's portfolio."""
    sql = "DELETE FROM portfolio WHERE user_id = %s AND stock_code = %s"
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (user_id, stock_code))
        conn.commit()
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_portfolio_by_user(user_id: int) -> list[dict[str, Any]]:
    """Return all portfolio items for a user."""
    sql = """
        SELECT stock_code, stock_name, added_at
        FROM portfolio
        WHERE user_id = %s
        ORDER BY added_at DESC
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, (user_id,))
        return [
            {"stock_code": r["stock_code"], "stock_name": r["stock_name"], "added_at": str(r["added_at"])}
            for r in cursor.fetchall()
        ]
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    try:
        result = get_latest_recommendations_json()
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    except Error as exc:
        print(f"MySQL error: {exc}")
