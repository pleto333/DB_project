from __future__ import annotations

import hashlib
import json
import os
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:  # Server still works in local fallback mode.
    mysql = None
    MySQLError = Exception


HOST = "127.0.0.1"
PORT = 5000
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = Path(__file__).with_name("local_state.json")
DB_READY = False
DB_ERROR = "not initialized"

SAMPLE_STOCKS = [
    {
        "rank": 1,
        "name": "삼성전자",
        "code": "005930",
        "price": "71,500 KRW",
        "change": 2.3,
        "reason": "반도체 수요 회복",
        "sparkline": "0,20 10,18 20,22 30,15 40,12 50,10 60,6",
    },
    {
        "rank": 2,
        "name": "SK하이닉스",
        "code": "000660",
        "price": "138,000 KRW",
        "change": 1.8,
        "reason": "HBM 수요 확대",
        "sparkline": "0,22 10,20 20,18 30,16 40,14 50,10 60,8",
    },
    {
        "rank": 3,
        "name": "NAVER",
        "code": "035420",
        "price": "182,500 KRW",
        "change": -0.5,
        "reason": "AI 서비스 확장",
        "sparkline": "0,8 10,10 20,12 30,14 40,16 50,18 60,20",
    },
    {
        "rank": 4,
        "name": "카카오",
        "code": "035720",
        "price": "42,300 KRW",
        "change": 0.9,
        "reason": "플랫폼 실적 회복",
        "sparkline": "0,18 10,16 20,20 30,14 40,12 50,10 60,8",
    },
    {
        "rank": 5,
        "name": "LG에너지솔루션",
        "code": "373220",
        "price": "312,000 KRW",
        "change": -1.2,
        "reason": "배터리 수주 모멘텀",
        "sparkline": "0,6 10,10 20,12 30,14 40,18 50,20 60,22",
    },
    {
        "rank": 6,
        "name": "현대차",
        "code": "005380",
        "price": "215,000 KRW",
        "change": 0.4,
        "reason": "수출 및 환율 수혜",
        "sparkline": "0,18 10,17 20,19 30,16 40,15 50,13 60,12",
    },
    {
        "rank": 7,
        "name": "삼성바이오로직스",
        "code": "207940",
        "price": "850,000 KRW",
        "change": -0.8,
        "reason": "바이오 위탁생산 수주",
        "sparkline": "0,8 10,9 20,12 30,13 40,17 50,20 60,21",
    },
]

MARKET_TICKERS = [
    {"name": "KOSPI", "value": "2,623.45", "change": 0.87},
    {"name": "KOSDAQ", "value": "748.32", "change": -0.43},
    {"name": "NASDAQ", "value": "19,245.30", "change": 1.24},
    {"name": "S&P500", "value": "5,308.12", "change": 0.62},
    {"name": "DOW", "value": "39,872.00", "change": -0.18},
    {"name": "USD/KRW", "value": "1,342 KRW", "change": -0.15},
]

ANALYSIS_FALLBACKS = {
    "005930": {
        "recommend": True,
        "confidence": 82,
        "summary": "반도체 업황 회복과 AI 서버 투자 확대가 메모리 수요 기대를 키우고 있어 단기 관심 종목으로 분류했습니다.",
        "positives": [
            "AI 서버와 HBM 수요 확대가 메모리 업황 회복 기대를 뒷받침합니다.",
            "주요 고객사의 고성능 반도체 투자 확대가 실적 개선 모멘텀으로 이어질 수 있습니다.",
            "대형주 특성상 시장 반등 구간에서 기관·외국인 수급 유입 가능성이 있습니다.",
        ],
        "negatives": [
            "메모리 가격 회복 속도가 예상보다 느리면 실적 기대가 낮아질 수 있습니다.",
            "환율과 글로벌 IT 수요 둔화가 단기 변동성을 키울 수 있습니다.",
        ],
        "detailAnalysis": "최근 뉴스 흐름은 AI 인프라 투자, HBM 공급 경쟁, 반도체 업황 회복 기대에 집중되어 있습니다. 삼성전자는 메모리와 파운드리 양쪽에 노출되어 있어 업황 개선 시 수혜 폭이 크지만, HBM 경쟁력 확인과 실적 회복 속도가 핵심 체크 포인트입니다. 따라서 현재 데이터 기준으로는 매수 관심 의견을 줄 수 있으나, 분기 실적과 HBM 공급 관련 후속 뉴스 확인이 필요합니다.",
        "relatedNews": [
            {
                "id": 1,
                "sentiment": "positive",
                "time": "오늘",
                "title": "AI 서버 투자 확대에 HBM·메모리 반도체 수요 기대",
                "desc": "AI 데이터센터 증설 흐름이 고성능 메모리 수요 회복 기대를 높이고 있습니다.",
            },
            {
                "id": 2,
                "sentiment": "positive",
                "time": "오늘",
                "title": "반도체 업황 회복 기대에 대형 IT주 관심 지속",
                "desc": "메모리 가격 반등과 재고 조정 마무리 기대가 대형 반도체주 수급에 영향을 주고 있습니다.",
            },
            {
                "id": 3,
                "sentiment": "negative",
                "time": "오늘",
                "title": "HBM 경쟁 심화와 고객사 인증 일정은 변수",
                "desc": "고부가 메모리 시장에서 경쟁사 대비 공급 속도와 수율 개선 여부가 중요 변수입니다.",
            },
        ],
    },
    "000660": {
        "recommend": True,
        "confidence": 86,
        "summary": "HBM 중심의 실적 모멘텀이 강해 AI 반도체 테마 내 관심도가 높은 종목입니다.",
        "positives": [
            "HBM 수요 확대가 매출 믹스 개선으로 이어질 수 있습니다.",
            "AI 가속기 공급망과 직접 연결된 뉴스 모멘텀이 있습니다.",
            "메모리 가격 회복 시 영업 레버리지 효과가 클 수 있습니다.",
        ],
        "negatives": [
            "주가에 AI·HBM 기대가 이미 일부 반영되어 밸류에이션 부담이 있습니다.",
            "고객사 투자 속도 변화에 민감합니다.",
        ],
        "detailAnalysis": "SK Hynix는 HBM 수요 확대의 직접 수혜주로 해석됩니다. 뉴스 기반 모멘텀은 긍정적이지만, 단기 급등 이후에는 고객사 주문 흐름과 공급 경쟁 변화에 따라 변동성이 커질 수 있습니다.",
        "relatedNews": [
            {
                "id": 1,
                "sentiment": "positive",
                "time": "오늘",
                "title": "AI 가속기 수요 증가로 HBM 공급 부족 전망",
                "desc": "고성능 메모리 수요가 빠르게 늘면서 HBM 공급 기업에 대한 관심이 이어지고 있습니다.",
            },
            {
                "id": 2,
                "sentiment": "neutral",
                "time": "오늘",
                "title": "메모리 업종, 실적 회복 속도 확인 필요",
                "desc": "업황 개선 기대는 유지되지만 분기별 가격과 출하량 확인이 필요합니다.",
            },
        ],
    },
    "035420": {
        "recommend": True,
        "confidence": 71,
        "summary": "AI 서비스와 클라우드 확장 기대가 있으나 광고·커머스 경기 영향도 함께 확인해야 합니다.",
        "positives": [
            "AI 검색과 기업용 AI 서비스 확장 기대가 있습니다.",
            "커머스와 콘텐츠 사업의 수익화 개선 가능성이 있습니다.",
        ],
        "negatives": [
            "광고 경기 둔화 시 매출 성장률이 제한될 수 있습니다.",
            "AI 투자 비용 증가가 단기 수익성을 압박할 수 있습니다.",
        ],
        "detailAnalysis": "NAVER는 AI 서비스 확장 뉴스가 긍정적이지만, 실제 실적 기여도와 비용 증가를 함께 봐야 합니다. 현재는 공격적 매수보다 관심 유지에 가까운 분석 결과입니다.",
        "relatedNews": [
            {
                "id": 1,
                "sentiment": "positive",
                "time": "오늘",
                "title": "AI 기반 검색·클라우드 서비스 확대",
                "desc": "기업 고객을 대상으로 한 AI 서비스 확대 기대가 제기되고 있습니다.",
            },
            {
                "id": 2,
                "sentiment": "negative",
                "time": "오늘",
                "title": "플랫폼 업종, 광고 경기 회복 속도는 변수",
                "desc": "광고 매출 회복이 지연될 경우 성장 기대가 낮아질 수 있습니다.",
            },
        ],
    },
    "035720": {
        "recommend": True,
        "confidence": 69,
        "summary": "카카오는 플랫폼 비용 효율화와 광고·커머스 회복 기대가 있으나, 신사업 성장 속도와 규제 이슈를 함께 봐야 합니다.",
        "positives": [
            "톡비즈와 커머스 회복이 실적 개선의 핵심 동력이 될 수 있습니다.",
            "비용 효율화가 이어질 경우 영업이익률 개선 기대가 있습니다.",
            "AI·콘텐츠·모빌리티 등 플랫폼 확장 옵션이 남아 있습니다.",
        ],
        "negatives": [
            "플랫폼 규제와 수수료 관련 이슈가 투자심리를 약화시킬 수 있습니다.",
            "광고 경기 회복이 지연되면 매출 반등이 제한될 수 있습니다.",
        ],
        "detailAnalysis": "카카오는 단기적으로 광고와 커머스 회복, 비용 통제 여부가 중요합니다. 뉴스 흐름상 플랫폼 업종 전반의 회복 기대는 있지만, 규제와 신사업 수익성 논란이 동시에 존재합니다. 따라서 강한 매수보다는 실적 개선 확인을 전제로 한 관심 의견이 적절합니다.",
        "relatedNews": [
            {
                "id": 1,
                "sentiment": "positive",
                "time": "오늘",
                "title": "플랫폼 업종, 광고·커머스 회복 기대",
                "desc": "내수 소비와 광고 집행 회복 기대가 플랫폼 기업 실적 반등 가능성을 높이고 있습니다.",
            },
            {
                "id": 2,
                "sentiment": "positive",
                "time": "오늘",
                "title": "비용 효율화 기조 지속 여부 주목",
                "desc": "수익성 중심 경영이 이어질 경우 영업이익률 개선이 가능하다는 분석이 나옵니다.",
            },
            {
                "id": 3,
                "sentiment": "negative",
                "time": "오늘",
                "title": "플랫폼 규제와 경쟁 심화는 부담",
                "desc": "수수료, 개인정보, 독점 규제 이슈는 주가 할인 요인으로 작용할 수 있습니다.",
            },
        ],
    },
    "373220": {
        "recommend": False,
        "confidence": 62,
        "summary": "LG에너지솔루션은 장기 배터리 수요는 유효하지만 전기차 수요 둔화와 판가 압박으로 단기 모멘텀은 제한적입니다.",
        "positives": [
            "북미 배터리 공급망 재편과 장기 수주잔고는 중장기 안정성을 제공합니다.",
            "ESS와 전력 저장 수요 확대는 새로운 성장 축이 될 수 있습니다.",
        ],
        "negatives": [
            "전기차 수요 둔화가 배터리 출하량과 가동률에 부담을 줄 수 있습니다.",
            "원재료 가격과 판가 하락 압력이 수익성을 압박할 수 있습니다.",
            "보조금 정책 변화와 고객사 생산 계획 조정에 민감합니다.",
        ],
        "detailAnalysis": "LG에너지솔루션은 배터리 대표주로 장기 성장성은 유지되지만, 단기 뉴스 흐름은 전기차 수요 둔화와 판가 압박에 더 민감합니다. 수주잔고와 북미 공급망 이점은 긍정적이나, 실적 반등이 확인되기 전까지는 보수적인 접근이 필요합니다.",
        "relatedNews": [
            {
                "id": 1,
                "sentiment": "positive",
                "time": "오늘",
                "title": "북미 배터리 공급망 재편 기대",
                "desc": "현지 생산과 장기 공급계약은 중장기 성장 기반으로 평가됩니다.",
            },
            {
                "id": 2,
                "sentiment": "neutral",
                "time": "오늘",
                "title": "ESS 수요 확대가 새 성장 축으로 부상",
                "desc": "전력망 투자와 데이터센터 전력 수요 증가가 ESS 시장 확대 기대를 만들고 있습니다.",
            },
            {
                "id": 3,
                "sentiment": "negative",
                "time": "오늘",
                "title": "전기차 수요 둔화와 판가 압박 지속",
                "desc": "완성차 업체의 생산 조정과 배터리 가격 하락은 단기 실적 부담으로 작용할 수 있습니다.",
            },
        ],
    },
}

GENERIC_ANALYSIS = {
    "recommend": True,
    "confidence": 68,
    "summary": "현재 뉴스와 가격 데이터를 바탕으로 만든 로컬 분석 결과입니다. 실제 LLM 분석은 API 키 연결 후 대체됩니다.",
    "positives": [
        "관심 종목으로 분류되어 가격과 포트폴리오 추적이 가능합니다.",
        "시장 테마와 연결될 경우 단기 수급 모멘텀이 발생할 수 있습니다.",
    ],
    "negatives": [
        "실제 뉴스 수집과 LLM 분석이 아직 연결되지 않아 근거 데이터가 제한적입니다.",
        "실적, 공시, 수급 데이터 확인 없이 투자 판단에 사용하면 위험합니다.",
    ],
    "detailAnalysis": "이 분석은 프론트엔드 연동 확인을 위한 로컬 fallback입니다. 실제 서비스에서는 LS 뉴스 수집 결과와 Gemini 응답 JSON을 저장한 뒤 이 필드를 교체해야 합니다.",
    "relatedNews": [
        {
            "id": 1,
            "sentiment": "neutral",
            "time": "오늘",
            "title": "로컬 fallback 분석 데이터 사용 중",
            "desc": "LS 뉴스 API와 Gemini 분석 결과가 연결되면 실제 근거 뉴스로 대체됩니다.",
        }
    ],
}


def _default_state() -> dict:
    return {
        "users": {
            "hong123": {
                "id": "hong123",
                "password": "password123",
                "email": "hong123@example.com",
                "nickname": "Demo User",
            }
        },
        "portfolio": {},
    }


def load_state() -> dict:
    if not DATA_FILE.exists():
        return _default_state()
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _default_state()


def save_state(state: dict) -> None:
    DATA_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_dotenv_file() -> None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


def password_hash(password: str) -> str:
    return hashlib.sha256(f"stockai:{password}".encode("utf-8")).hexdigest()


def db_config(include_database: bool = True) -> dict:
    load_dotenv_file()
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "charset": "utf8mb4",
        "use_unicode": True,
    }
    if include_database:
        config["database"] = os.getenv("DB_NAME", "stock_prediction_db")
    return config


def db_connect(include_database: bool = True):
    if mysql is None:
        raise RuntimeError("mysql-connector-python is not installed")
    return mysql.connector.connect(**db_config(include_database=include_database))


def db_execute_schema(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            email VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT uk_users_username UNIQUE (username),
            CONSTRAINT uk_users_email UNIQUE (email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stocks (
            stock_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            stock_code VARCHAR(20) NOT NULL,
            stock_name VARCHAR(100) NOT NULL,
            market ENUM('KOSPI', 'KOSDAQ', 'NASDAQ', 'NYSE', 'OTHER') NOT NULL DEFAULT 'KOSPI',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT uk_stocks_stock_code UNIQUE (stock_code),
            INDEX idx_stocks_stock_name (stock_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_holdings (
            holding_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT UNSIGNED NOT NULL,
            stock_id BIGINT UNSIGNED NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT uk_user_holdings_user_stock UNIQUE (user_id, stock_id),
            CONSTRAINT fk_user_holdings_user
                FOREIGN KEY (user_id) REFERENCES users (user_id)
                ON UPDATE CASCADE
                ON DELETE CASCADE,
            CONSTRAINT fk_user_holdings_stock
                FOREIGN KEY (stock_id) REFERENCES stocks (stock_id)
                ON UPDATE CASCADE
                ON DELETE CASCADE,
            INDEX idx_user_holdings_user_id (user_id),
            INDEX idx_user_holdings_stock_id (stock_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS news_articles (
            article_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(300) NOT NULL,
            summary TEXT NULL,
            url VARCHAR(1000) NOT NULL,
            url_hash CHAR(64) NOT NULL,
            publisher VARCHAR(100) NULL,
            source VARCHAR(50) NOT NULL DEFAULT 'ls_securities',
            published_at DATETIME NULL,
            collected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT uk_news_articles_url_hash UNIQUE (url_hash),
            INDEX idx_news_articles_published_at (published_at),
            INDEX idx_news_articles_collected_at (collected_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS llm_analysis (
            analysis_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT UNSIGNED NULL,
            model_name VARCHAR(100) NOT NULL,
            input_summary TEXT NOT NULL,
            response_json JSON NOT NULL,
            analyzed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_llm_analysis_user
                FOREIGN KEY (user_id) REFERENCES users (user_id)
                ON UPDATE CASCADE
                ON DELETE SET NULL,
            INDEX idx_llm_analysis_user_id (user_id),
            INDEX idx_llm_analysis_analyzed_at (analyzed_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stock_recommendations (
            recommendation_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            analysis_id BIGINT UNSIGNED NOT NULL,
            stock_id BIGINT UNSIGNED NOT NULL,
            rank_no INT UNSIGNED NOT NULL,
            recommendation ENUM('BUY', 'WATCH') NOT NULL DEFAULT 'WATCH',
            reason TEXT NOT NULL,
            confidence DECIMAL(5, 4) NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT uk_stock_recommendations_analysis_rank UNIQUE (analysis_id, rank_no),
            CONSTRAINT chk_stock_recommendations_confidence CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
            CONSTRAINT fk_stock_recommendations_analysis
                FOREIGN KEY (analysis_id) REFERENCES llm_analysis (analysis_id)
                ON UPDATE CASCADE
                ON DELETE CASCADE,
            CONSTRAINT fk_stock_recommendations_stock
                FOREIGN KEY (stock_id) REFERENCES stocks (stock_id)
                ON UPDATE CASCADE
                ON DELETE RESTRICT,
            INDEX idx_stock_recommendations_analysis_id (analysis_id),
            INDEX idx_stock_recommendations_stock_id (stock_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def db_seed(cursor) -> None:
    for stock in SAMPLE_STOCKS:
        cursor.execute(
            """
            INSERT INTO stocks (stock_code, stock_name, market)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                stock_name = VALUES(stock_name),
                market = VALUES(market)
            """,
            (stock["code"], stock["name"], "KOSPI"),
        )

    cursor.execute(
        """
        INSERT INTO users (username, email, password_hash)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            email = VALUES(email)
        """,
        ("hong123", "hong123@example.com", password_hash("password123")),
    )


def initialize_database() -> tuple[bool, str]:
    try:
        database_name = db_config(include_database=True)["database"]
        conn = db_connect(include_database=False)
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
            "DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        cursor.close()
        conn.close()

        conn = db_connect(include_database=True)
        cursor = conn.cursor()
        db_execute_schema(cursor)
        db_seed(cursor)
        conn.commit()
        cursor.close()
        conn.close()
        return True, ""
    except Exception as exc:
        return False, str(exc)


def ensure_database_ready() -> bool:
    global DB_READY, DB_ERROR
    if DB_READY:
        return True
    DB_READY, DB_ERROR = initialize_database()
    return DB_READY


def db_try(callback):
    global DB_READY, DB_ERROR
    if not ensure_database_ready():
        return None
    try:
        return callback()
    except Exception as exc:
        DB_READY = False
        DB_ERROR = str(exc)
        return None


def db_get_or_create_user_id(username: str, password: str = "password123", email: str | None = None) -> int:
    conn = db_connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if row:
            return int(row[0])

        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email or f"{username}@local.test", password_hash(password)),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        cursor.close()
        conn.close()


def db_register_user(username: str, password: str, email: str, nickname: str = "") -> dict:
    conn = db_connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash(password)),
        )
        conn.commit()
        return {"id": username, "email": email, "nickname": nickname or username}
    finally:
        cursor.close()
        conn.close()


def db_login_user(username: str, password: str) -> dict | None:
    conn = db_connect()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT username, email, password_hash FROM users WHERE username = %s",
            (username,),
        )
        row = cursor.fetchone()
        if not row or row["password_hash"] != password_hash(password):
            return None
        return {"id": row["username"], "email": row["email"], "nickname": row["username"]}
    finally:
        cursor.close()
        conn.close()


def db_stock_to_ui(row: dict, fallback: dict | None = None) -> dict:
    base = dict(fallback or {})
    base.update(
        {
            "name": row["stock_name"],
            "code": row["stock_code"],
            "market": row.get("market", "KOSPI"),
        }
    )
    return quote_stock(base)


def db_get_stock(code: str) -> dict:
    conn = db_connect()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT stock_code, stock_name, market FROM stocks WHERE stock_code = %s",
            (code,),
        )
        row = cursor.fetchone()
        fallback = find_stock(code)
        return db_stock_to_ui(row, fallback) if row else quote_stock(fallback)
    finally:
        cursor.close()
        conn.close()


def db_list_recommended_stocks() -> list[dict]:
    conn = db_connect()
    cursor = conn.cursor(dictionary=True)
    try:
        codes = [stock["code"] for stock in SAMPLE_STOCKS[:5]]
        placeholders = ", ".join(["%s"] * len(codes))
        cursor.execute(
            f"""
            SELECT stock_code, stock_name, market
            FROM stocks
            WHERE stock_code IN ({placeholders})
            """,
            tuple(codes),
        )
        rows = {row["stock_code"]: row for row in cursor.fetchall()}
        result = []
        for fallback in SAMPLE_STOCKS[:5]:
            row = rows.get(fallback["code"])
            result.append(db_stock_to_ui(row, fallback) if row else quote_stock(fallback))
        return result
    finally:
        cursor.close()
        conn.close()


def db_search_stocks(query: str) -> list[dict]:
    conn = db_connect()
    cursor = conn.cursor(dictionary=True)
    try:
        like = f"%{query}%"
        cursor.execute(
            """
            SELECT stock_code, stock_name, market
            FROM stocks
            WHERE stock_code LIKE %s OR stock_name LIKE %s
            ORDER BY stock_code
            LIMIT 20
            """,
            (like, like),
        )
        return [db_stock_to_ui(row, find_stock(row["stock_code"])) for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def db_upsert_stock_from_payload(stock_code: str, stock_name: str) -> int:
    stock = next((item for item in SAMPLE_STOCKS if item["code"] == stock_code), {})
    stock_name = stock.get("name") or stock_name or stock_code
    conn = db_connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO stocks (stock_code, stock_name, market)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                stock_id = LAST_INSERT_ID(stock_id),
                stock_name = VALUES(stock_name),
                market = VALUES(market)
            """,
            (stock_code, stock_name, "KOSPI"),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        cursor.close()
        conn.close()


def db_get_portfolio(username: str) -> list[dict]:
    user_pk = db_get_or_create_user_id(username)
    conn = db_connect()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT s.stock_code, s.stock_name, s.market
            FROM user_holdings h
            JOIN stocks s ON s.stock_id = h.stock_id
            WHERE h.user_id = %s
            ORDER BY h.created_at, h.holding_id
            """,
            (user_pk,),
        )
        return [db_stock_to_ui(row, find_stock(row["stock_code"])) for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def db_add_portfolio(username: str, stock_code: str, stock_name: str) -> list[dict]:
    user_pk = db_get_or_create_user_id(username)
    stock_pk = db_upsert_stock_from_payload(stock_code, stock_name)
    conn = db_connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT IGNORE INTO user_holdings (user_id, stock_id) VALUES (%s, %s)",
            (user_pk, stock_pk),
        )
        conn.commit()
        return db_get_portfolio(username)
    finally:
        cursor.close()
        conn.close()


def db_remove_portfolio(username: str, stock_code: str) -> list[dict]:
    user_pk = db_get_or_create_user_id(username)
    conn = db_connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            DELETE h
            FROM user_holdings h
            JOIN stocks s ON s.stock_id = h.stock_id
            WHERE h.user_id = %s AND s.stock_code = %s
            """,
            (user_pk, stock_code),
        )
        conn.commit()
        return db_get_portfolio(username)
    finally:
        cursor.close()
        conn.close()


def fetch_naver_price(code: str) -> str | None:
    """Best-effort free quote lookup. Falls back silently when offline or changed."""
    if not re.fullmatch(r"\d{6}", code):
        return None

    url = f"https://finance.naver.com/item/main.naver?code={code}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=2.5) as response:
            html = response.read().decode("euc-kr", errors="ignore")
    except Exception:
        return None

    match = re.search(
        r'<p class="no_today">.*?<span class="blind">([\d,]+)</span>',
        html,
        flags=re.DOTALL,
    )
    if not match:
        return None

    return f"{match.group(1)} KRW"


def quote_stock(stock: dict) -> dict:
    quoted = dict(stock)
    live_price = fetch_naver_price(str(stock.get("code", "")))
    if live_price:
        quoted["price"] = live_price
        quoted["quote_source"] = "naver_finance"
    else:
        quoted["quote_source"] = "local_fallback"
    return quoted


def find_stock(code: str) -> dict:
    return next((item for item in SAMPLE_STOCKS if item["code"] == code), SAMPLE_STOCKS[0])


def refresh_portfolio_prices(items: list[dict]) -> list[dict]:
    refreshed = []
    for item in items:
        stock = find_stock(str(item.get("code", "")))
        refreshed_stock = quote_stock({**item, **stock})
        refreshed.append(refreshed_stock)
    return refreshed


def build_stock_analysis(stock: dict) -> dict:
    analysis = ANALYSIS_FALLBACKS.get(str(stock.get("code", "")), GENERIC_ANALYSIS)
    return {
        **stock,
        **analysis,
        "analysis_source": "local_fallback",
    }


class ApiHandler(BaseHTTPRequestHandler):
    server_version = "StockAIBackend/0.1"

    def do_OPTIONS(self) -> None:
        self._send_empty()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            db_connected = ensure_database_ready()
            self._send_json(
                {
                    "ok": True,
                    "db": {
                        "connected": db_connected,
                        "name": os.getenv("DB_NAME", "stock_prediction_db"),
                        "error": "" if db_connected else DB_ERROR,
                    },
                }
            )
            return

        if parsed.path == "/market/tickers":
            self._send_json(MARKET_TICKERS)
            return

        if parsed.path == "/stocks/recommended":
            db_result = db_try(db_list_recommended_stocks)
            self._send_json(db_result if db_result is not None else [quote_stock(stock) for stock in SAMPLE_STOCKS[:5]])
            return

        if parsed.path == "/stocks/search":
            query = parse_qs(parsed.query).get("query", [""])[0].lower()
            db_result = db_try(lambda: db_search_stocks(query))
            if db_result is not None:
                self._send_json(db_result)
                return
            results = [
                quote_stock(stock)
                for stock in SAMPLE_STOCKS
                if query in stock["name"].lower() or query in stock["code"]
            ]
            self._send_json(results)
            return

        if parsed.path.startswith("/stocks/") and parsed.path.endswith("/analysis"):
            code = parsed.path.split("/")[2]
            stock = db_try(lambda: db_get_stock(code)) or quote_stock(find_stock(code))
            self._send_json(build_stock_analysis(stock))
            return

        if parsed.path == "/portfolio":
            user_id = parse_qs(parsed.query).get("user_id", ["hong123"])[0]
            db_result = db_try(lambda: db_get_portfolio(user_id))
            if db_result is not None:
                self._send_json(db_result)
                return
            state = load_state()
            portfolio = refresh_portfolio_prices(state.get("portfolio", {}).get(user_id, []))
            state.setdefault("portfolio", {})[user_id] = portfolio
            save_state(state)
            self._send_json(portfolio)
            return

        self._send_json({"message": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        body = self._read_json()
        state = load_state()

        if parsed.path == "/register":
            user_id = str(body.get("id", "")).strip()
            password = str(body.get("password", "")).strip()
            email = str(body.get("email", "")).strip()
            nickname = str(body.get("nickname", "")).strip()
            if not user_id or not password:
                self._send_json({"message": "id and password are required"}, HTTPStatus.BAD_REQUEST)
                return

            if ensure_database_ready():
                try:
                    db_result = db_register_user(user_id, password, email, nickname)
                    self._send_json({"message": "registered", "user": db_result})
                except Exception as exc:
                    status = HTTPStatus.CONFLICT if "Duplicate" in str(exc) else HTTPStatus.INTERNAL_SERVER_ERROR
                    self._send_json({"message": str(exc)}, status)
                return

            if user_id in state["users"]:
                self._send_json({"message": "User already exists"}, HTTPStatus.CONFLICT)
                return
            state["users"][user_id] = {
                "id": user_id,
                "password": password,
                "email": email,
                "nickname": nickname or user_id,
            }
            save_state(state)
            self._send_json({"message": "registered", "user": {"id": user_id}})
            return

        if parsed.path == "/login":
            user_id = str(body.get("id", "")).strip()
            password = str(body.get("password", "")).strip()
            if ensure_database_ready():
                try:
                    db_result = db_login_user(user_id, password)
                except Exception as exc:
                    self._send_json({"message": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
                    return
                if not db_result:
                    self._send_json({"message": "Invalid id or password"}, HTTPStatus.UNAUTHORIZED)
                    return
                self._send_json({"message": "logged in", "user": db_result})
                return

            user = state["users"].get(user_id)
            if not user or user["password"] != password:
                self._send_json({"message": "Invalid id or password"}, HTTPStatus.UNAUTHORIZED)
                return
            self._send_json(
                {
                    "message": "logged in",
                    "user": {
                        "id": user["id"],
                        "email": user.get("email", ""),
                        "nickname": user.get("nickname", user["id"]),
                    },
                }
            )
            return

        if parsed.path == "/portfolio":
            user_id = str(body.get("user_id", "hong123")).strip() or "hong123"
            stock_code = str(body.get("stock_code", "")).strip()
            stock_name = str(body.get("stock_name", "")).strip() or stock_code
            if not stock_code:
                self._send_json({"message": "stock_code is required"}, HTTPStatus.BAD_REQUEST)
                return

            db_result = db_try(lambda: db_add_portfolio(user_id, stock_code, stock_name))
            if db_result is not None:
                self._send_json({"message": "added", "portfolio": db_result})
                return

            portfolio = state.setdefault("portfolio", {}).setdefault(user_id, [])
            if not any(item["code"] == stock_code for item in portfolio):
                sample = quote_stock(find_stock(stock_code))
                portfolio.append(
                    {
                        "code": stock_code,
                        "name": sample.get("name", stock_name),
                        "price": sample.get("price", "-"),
                        "change": sample.get("change", 0),
                        "rank": sample.get("rank", len(portfolio) + 1),
                        "sparkline": sample.get("sparkline", "0,16 10,14 20,18 30,12 40,14 50,9 60,11"),
                    }
                )
            save_state(state)
            self._send_json({"message": "added", "portfolio": portfolio})
            return

        self._send_json({"message": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        body = self._read_json()
        if parsed.path != "/portfolio":
            self._send_json({"message": "Not found"}, HTTPStatus.NOT_FOUND)
            return

        user_id = str(body.get("user_id", "hong123")).strip() or "hong123"
        stock_code = str(body.get("stock_code", "")).strip()

        db_result = db_try(lambda: db_remove_portfolio(user_id, stock_code))
        if db_result is not None:
            self._send_json({"message": "removed", "portfolio": db_result})
            return

        state = load_state()
        portfolio = state.setdefault("portfolio", {}).setdefault(user_id, [])
        state["portfolio"][user_id] = [item for item in portfolio if item["code"] != stock_code]
        save_state(state)
        self._send_json({"message": "removed", "portfolio": state["portfolio"][user_id]})

    def log_message(self, format: str, *args) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0") or 0)
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _send_empty(self, status: HTTPStatus = HTTPStatus.NO_CONTENT) -> None:
        self.send_response(status)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ApiHandler)
    print(f"StockAI local backend running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
