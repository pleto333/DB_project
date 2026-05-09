from __future__ import annotations

import hashlib
import os
from typing import Any

import mysql.connector
from mysql.connector import Error


def get_connection() -> mysql.connector.MySQLConnection:
    """MySQL DB 연결 객체를 생성한다.

    환경변수를 사용하면 비밀번호를 코드에 직접 적지 않아도 된다.
    PowerShell 예시:
        $env:DB_USER="root"
        $env:DB_PASSWORD="내비밀번호"
    """
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "stock_prediction_db"),
        charset="utf8mb4",
        use_unicode=True,
    )


def _make_sentiment_label(sentiment_score: int) -> str:
    """감성 점수(-1, 0, 1)를 DB ENUM 값으로 변환한다."""
    if sentiment_score == 1:
        return "Positive"
    if sentiment_score == -1:
        return "Negative"
    if sentiment_score == 0:
        return "Neutral"
    raise ValueError("sentiment_score는 -1, 0, 1 중 하나여야 합니다.")


def _hash_url(url: str) -> str:
    """긴 URL을 UNIQUE 인덱스로 관리하기 위해 SHA-256 해시로 변환한다."""
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()


def add_user(
    username: str,
    email: str,
    password_hash: str,
    full_name: str | None = None,
    phone_number: str | None = None,
) -> int:
    """사용자 정보를 추가하고 생성된 user_id를 반환한다."""
    sql = """
        INSERT INTO users (username, email, password_hash, full_name, phone_number)
        VALUES (%s, %s, %s, %s, %s)
    """

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (username, email, password_hash, full_name, phone_number))
        conn.commit()
        return cursor.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def add_stock(
    stock_code: str,
    stock_name: str,
    market: str = "KOSPI",
    currency: str = "KRW",
    sector: str | None = None,
) -> int:
    """주식 기본 정보를 추가하거나 갱신하고 stock_id를 반환한다."""
    sql = """
        INSERT INTO stocks (stock_code, stock_name, market, currency, sector)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            stock_id = LAST_INSERT_ID(stock_id),
            stock_name = VALUES(stock_name),
            market = VALUES(market),
            currency = VALUES(currency),
            sector = VALUES(sector)
    """

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (stock_code, stock_name, market, currency, sector))
        conn.commit()
        return cursor.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def add_user_holding(
    user_id: int,
    stock_id: int,
    quantity: float,
    average_buy_price: float,
    buy_date: str,
    memo: str | None = None,
) -> int:
    """사용자 보유 주식을 추가한다.

    현재 설계는 사용자 1명이 같은 종목을 하나의 보유 행으로 관리한다.
    같은 user_id + stock_id가 다시 들어오면 수량과 평균 매수가를 갱신한다.
    """
    sql = """
        INSERT INTO user_holdings
            (user_id, stock_id, quantity, average_buy_price, buy_date, memo)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            holding_id = LAST_INSERT_ID(holding_id),
            quantity = VALUES(quantity),
            average_buy_price = VALUES(average_buy_price),
            buy_date = VALUES(buy_date),
            memo = VALUES(memo)
    """

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (user_id, stock_id, quantity, average_buy_price, buy_date, memo))
        conn.commit()
        return cursor.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def save_stock_price(
    stock_id: int,
    current_price: float,
    open_price: float | None = None,
    high_price: float | None = None,
    low_price: float | None = None,
    close_price: float | None = None,
    trading_volume: int | None = None,
    source: str = "manual",
    collected_at: str | None = None,
) -> int:
    """주식 현재가/시세 정보를 저장하고 price_id를 반환한다."""
    sql = """
        INSERT INTO stock_prices (
            stock_id, current_price, open_price, high_price, low_price,
            close_price, trading_volume, source, collected_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP))
        ON DUPLICATE KEY UPDATE
            price_id = LAST_INSERT_ID(price_id),
            current_price = VALUES(current_price),
            open_price = VALUES(open_price),
            high_price = VALUES(high_price),
            low_price = VALUES(low_price),
            close_price = VALUES(close_price),
            trading_volume = VALUES(trading_volume)
    """

    values = (
        stock_id,
        current_price,
        open_price,
        high_price,
        low_price,
        close_price,
        trading_volume,
        source,
        collected_at,
    )

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, values)
        conn.commit()
        return cursor.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def save_news_article(
    stock_id: int,
    title: str,
    url: str,
    summary: str | None = None,
    publisher: str | None = None,
    source: str = "google_news_rss",
    language: str = "ko",
    published_at: str | None = None,
    collected_at: str | None = None,
) -> int:
    """뉴스 기사 정보를 저장하고 article_id를 반환한다."""
    url_hash = _hash_url(url)
    sql = """
        INSERT INTO news_articles (
            stock_id, title, summary, url, url_hash, publisher,
            source, language, published_at, collected_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP))
        ON DUPLICATE KEY UPDATE
            article_id = LAST_INSERT_ID(article_id),
            title = VALUES(title),
            summary = VALUES(summary),
            publisher = VALUES(publisher),
            source = VALUES(source),
            language = VALUES(language),
            published_at = VALUES(published_at),
            collected_at = VALUES(collected_at)
    """

    values = (
        stock_id,
        title,
        summary,
        url,
        url_hash,
        publisher,
        source,
        language,
        published_at,
        collected_at,
    )

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, values)
        conn.commit()
        return cursor.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def save_sentiment_analysis(
    article_id: int,
    sentiment_score: int,
    confidence: float | None = None,
    analyzed_model: str = "rule_based_v1",
    analyzed_at: str | None = None,
) -> int:
    """뉴스 감성 분석 결과를 저장한다.

    sentiment_score 규칙:
        Positive = 1, Neutral = 0, Negative = -1
    """
    sentiment_label = _make_sentiment_label(sentiment_score)
    sql = """
        INSERT INTO sentiment_analysis (
            article_id, sentiment_label, sentiment_score,
            confidence, analyzed_model, analyzed_at
        )
        VALUES (%s, %s, %s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP))
        ON DUPLICATE KEY UPDATE
            sentiment_id = LAST_INSERT_ID(sentiment_id),
            sentiment_label = VALUES(sentiment_label),
            sentiment_score = VALUES(sentiment_score),
            confidence = VALUES(confidence),
            analyzed_model = VALUES(analyzed_model),
            analyzed_at = VALUES(analyzed_at)
    """

    values = (article_id, sentiment_label, sentiment_score, confidence, analyzed_model, analyzed_at)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, values)
        conn.commit()
        return cursor.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def save_stock_prediction(
    stock_id: int,
    prediction_date: str,
    prediction_direction: str,
    predicted_change_rate: float | None = None,
    predicted_price: float | None = None,
    sentiment_avg_score: float | None = None,
    confidence: float | None = None,
    basis_start_at: str | None = None,
    basis_end_at: str | None = None,
    model_name: str = "sentiment_average_model",
    model_version: str = "v1",
) -> int:
    """주가 예측 결과를 저장한다."""
    sql = """
        INSERT INTO stock_predictions (
            stock_id, prediction_date, prediction_direction, predicted_change_rate,
            predicted_price, sentiment_avg_score, confidence, basis_start_at,
            basis_end_at, model_name, model_version
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            prediction_id = LAST_INSERT_ID(prediction_id),
            prediction_direction = VALUES(prediction_direction),
            predicted_change_rate = VALUES(predicted_change_rate),
            predicted_price = VALUES(predicted_price),
            sentiment_avg_score = VALUES(sentiment_avg_score),
            confidence = VALUES(confidence),
            basis_start_at = VALUES(basis_start_at),
            basis_end_at = VALUES(basis_end_at)
    """

    values = (
        stock_id,
        prediction_date,
        prediction_direction,
        predicted_change_rate,
        predicted_price,
        sentiment_avg_score,
        confidence,
        basis_start_at,
        basis_end_at,
        model_name,
        model_version,
    )

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, values)
        conn.commit()
        return cursor.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def save_user_report(
    user_id: int,
    stock_id: int,
    report_title: str,
    report_content: str,
    prediction_id: int | None = None,
    profit_rate: float | None = None,
    profit_amount: float | None = None,
    recommendation: str = "HOLD",
    generated_at: str | None = None,
) -> int:
    """사용자별 최종 투자 리포트를 저장한다."""
    sql = """
        INSERT INTO user_reports (
            user_id, stock_id, prediction_id, report_title, report_content,
            profit_rate, profit_amount, recommendation, generated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP))
        ON DUPLICATE KEY UPDATE
            report_id = LAST_INSERT_ID(report_id),
            prediction_id = VALUES(prediction_id),
            report_title = VALUES(report_title),
            report_content = VALUES(report_content),
            profit_rate = VALUES(profit_rate),
            profit_amount = VALUES(profit_amount),
            recommendation = VALUES(recommendation)
    """

    values = (
        user_id,
        stock_id,
        prediction_id,
        report_title,
        report_content,
        profit_rate,
        profit_amount,
        recommendation,
        generated_at,
    )

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, values)
        conn.commit()
        return cursor.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_user_holdings_with_profit(user_id: int) -> list[dict[str, Any]]:
    """사용자별 보유 주식과 현재 수익률을 조회한다."""
    sql = """
        SELECT
            h.holding_id,
            h.user_id,
            s.stock_id,
            s.stock_code,
            s.stock_name,
            h.quantity,
            h.average_buy_price,
            h.buy_date,
            lp.current_price,
            lp.collected_at AS price_collected_at,
            ROUND((lp.current_price - h.average_buy_price) * h.quantity, 4) AS profit_amount,
            ROUND(((lp.current_price - h.average_buy_price) / h.average_buy_price) * 100, 4) AS profit_rate
        FROM user_holdings h
        JOIN stocks s ON s.stock_id = h.stock_id
        LEFT JOIN stock_prices lp
            ON lp.price_id = (
                SELECT sp.price_id
                FROM stock_prices sp
                WHERE sp.stock_id = h.stock_id
                ORDER BY sp.collected_at DESC, sp.price_id DESC
                LIMIT 1
            )
        WHERE h.user_id = %s
        ORDER BY s.stock_name
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, (user_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_user_reports(user_id: int) -> list[dict[str, Any]]:
    """사용자별 최종 투자 리포트를 최신순으로 조회한다."""
    sql = """
        SELECT
            r.report_id,
            r.user_id,
            s.stock_code,
            s.stock_name,
            r.report_title,
            r.report_content,
            r.profit_rate,
            r.profit_amount,
            r.recommendation,
            r.generated_at,
            p.prediction_direction,
            p.predicted_change_rate,
            p.predicted_price,
            p.sentiment_avg_score
        FROM user_reports r
        JOIN stocks s ON s.stock_id = r.stock_id
        LEFT JOIN stock_predictions p ON p.prediction_id = r.prediction_id
        WHERE r.user_id = %s
        ORDER BY r.generated_at DESC, r.report_id DESC
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, (user_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # 간단한 연결 테스트용 코드다.
    # 실제 실행 전 sql/schema.sql과 sql/sample_data.sql을 먼저 실행해야 한다.
    try:
        rows = get_user_holdings_with_profit(user_id=1)
        for row in rows:
            print(row)
    except Error as exc:
        print(f"MySQL 연결 또는 쿼리 실행 중 오류가 발생했습니다: {exc}")
