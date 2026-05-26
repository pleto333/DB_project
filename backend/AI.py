"""
LS Securities news -> Gemini analysis end-to-end sample.

Required packages:
    pip install google-genai python-dotenv requests websockets

.env.example:
    GEMINI_API_KEY=your_gemini_api_key
    GEMINI_MODEL=gemini-2.5-flash
    GEMINI_FALLBACK_MODELS=gemini-2.0-flash,gemini-2.5-flash-lite
    GEMINI_MAX_RETRIES=3
    LS_APP_KEY=your_ls_app_key
    LS_APP_SECRET=your_ls_app_secret
    LS_ACCESS_TOKEN=optional_existing_access_token
    LS_TOKEN_URL=https://openapi.ls-sec.co.kr:8080/oauth2/token
    LS_NEWS_API_URL=https://openapi.ls-sec.co.kr:8080/stock/investinfo
    LS_NEWS_WS_URL=wss://openapi.ls-sec.co.kr:9443/websocket
    LS_NEWS_WS_TR_KEY=NWS001
    LS_NEWS_WS_TIMEOUT=30
    LS_NEWS_WS_SSL_VERIFY=false
    LS_NEWS_MAX_ATTEMPTS=5
    USE_DUMMY_AI=false
    USE_SAMPLE_NEWS=false
    LS_NEWS_HOT_CODE=2023051510383935PL7HQ87D
    LS_NEWS_DATE=20230515
    LS_NEWS_TIME=103839
    LS_NEWS_SEQ=
"""

import html
import asyncio
import json
import os
import re
import ssl
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from google import genai


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_FALLBACK_MODELS = ["gemini-2.0-flash", "gemini-2.5-flash-lite"]
DEPRECATED_GEMINI_MODELS = {
    "gemini-1.5-flash",
    "models/gemini-1.5-flash",
}
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LS_DEFAULT_TOKEN_URL = "https://openapi.ls-sec.co.kr:8080/oauth2/token"
LS_DEFAULT_NEWS_API_URL = "https://openapi.ls-sec.co.kr:8080/stock/investinfo"
LS_DEFAULT_NEWS_WS_URL = "wss://openapi.ls-sec.co.kr:9443/websocket"
LS_DEFAULT_NEWS_WS_TR_KEY = "NWS001"
LS_NEWS_TR_CODE = "t3102"
LS_REQUEST_TIMEOUT = 10
MAX_FALLBACK_JSON_CHARS = 4000
NO_NEWS_DATA_MESSAGES = (
    "해당자료가 없습니다",
    "해당 자료가 없습니다",
    "다시 조회 바랍니다",
)


def get_sample_news_data() -> str:
    """Return sample Korean market news so Gemini flow can be tested without LS API."""
    return """
[샘플 뉴스 데이터]
1. 날짜: 2026-05-26
   제목: AI 반도체 수요 확대에 국내 HBM 및 첨단 패키징 관련주 관심
   내용: 글로벌 빅테크의 AI 서버 투자가 이어지면서 고대역폭 메모리, 반도체 장비,
   첨단 패키징 기업에 대한 시장 관심이 커지고 있다. 다만 단기 급등 부담과
   고객사 투자 속도 변화는 리스크로 지적된다.

2. 날짜: 2026-05-26
   제목: 전력 인프라 투자 확대 기대, 변압기와 전선 업종 수주 모멘텀 부각
   내용: 데이터센터와 재생에너지 설비 증가로 전력망 증설 필요성이 커지며
   변압기, 전선, 전력기기 기업의 해외 수주 기대가 높아지고 있다.

3. 날짜: 2026-05-26
   제목: 조선 업황 개선 기대 지속, LNG선과 친환경 선박 발주 주목
   내용: 주요 조선사의 수주 잔고가 높은 수준을 유지하고 있으며 LNG 운반선,
   친환경 선박 관련 기자재 기업도 함께 주목받고 있다. 원자재 가격과 환율은
   수익성 변수로 거론된다.

4. 날짜: 2026-05-26
   제목: 바이오 업종, 기술이전 및 임상 결과 발표 기대감 혼재
   내용: 일부 바이오 기업이 글로벌 학회와 임상 데이터 발표를 앞두고 관심을
   받고 있으나, 임상 실패 가능성과 자금 조달 리스크에 대한 주의가 필요하다.
""".strip()


def get_dummy_analysis_result() -> dict[str, Any]:
    """Return a fixed response for teammates without LS/Gemini API keys."""
    today = datetime.now().strftime("%Y-%m-%d")
    return {
        "analysis_date": today,
        "top_themes": [
            "AI 반도체",
            "전력 인프라",
            "조선",
        ],
        "recommendations": [
            {
                "rank": 1,
                "stock_name": "SK하이닉스",
                "stock_code": "000660",
                "market": "KOSPI",
                "theme": "AI 반도체/HBM",
                "reason": "더미 뉴스에서 AI 서버 투자 확대와 HBM 수요 증가가 언급되어 관련 모멘텀 예시로 선정했습니다.",
                "news_evidence": "AI 서버 투자 확대와 고대역폭 메모리 수요 증가 관련 예시 뉴스",
                "expected_momentum": "HBM 수요 확대 기대에 따른 단기 관심 증가",
                "risk": "반도체 업황 변동성과 단기 급등 부담",
                "confidence": "상",
            },
            {
                "rank": 2,
                "stock_name": "LS ELECTRIC",
                "stock_code": "010120",
                "market": "KOSPI",
                "theme": "전력 인프라",
                "reason": "데이터센터 전력 수요와 전력기기 수주 기대를 반영한 더미 추천입니다.",
                "news_evidence": "데이터센터와 재생에너지 설비 증가로 전력망 증설 필요성 부각",
                "expected_momentum": "전력기기 수주 기대에 따른 시장 관심",
                "risk": "원자재 가격, 환율, 수주 지연 가능성",
                "confidence": "상",
            },
            {
                "rank": 3,
                "stock_name": "HD한국조선해양",
                "stock_code": "009540",
                "market": "KOSPI",
                "theme": "조선/LNG선",
                "reason": "LNG선 및 친환경 선박 발주 기대를 반영한 예시 결과입니다.",
                "news_evidence": "조선 업황 개선과 높은 수주잔고 관련 예시 뉴스",
                "expected_momentum": "수주잔고와 친환경 선박 발주 기대",
                "risk": "후판 가격, 환율, 선가 변동",
                "confidence": "중",
            },
            {
                "rank": 4,
                "stock_name": "한미반도체",
                "stock_code": "042700",
                "market": "KOSDAQ",
                "theme": "첨단 패키징",
                "reason": "HBM 생산 확대에 필요한 장비 수요 증가를 가정한 더미 추천입니다.",
                "news_evidence": "첨단 패키징 장비 기업 관심 확대 예시 뉴스",
                "expected_momentum": "AI 반도체 투자 확대에 따른 장비 수요",
                "risk": "고객사 투자 속도와 반도체 장비 사이클 변동",
                "confidence": "중",
            },
            {
                "rank": 5,
                "stock_name": "삼성SDS",
                "stock_code": "018260",
                "market": "KOSPI",
                "theme": "AI/클라우드",
                "reason": "기업의 AI 도입과 클라우드 전환 수요 증가를 반영한 더미 추천입니다.",
                "news_evidence": "기업 생산성 향상을 위한 AI 솔루션 도입 확대 예시 뉴스",
                "expected_momentum": "AI 기반 업무 자동화 및 클라우드 수요 증가",
                "risk": "IT 투자 지연, 경쟁 심화",
                "confidence": "중",
            },
        ],
        "overall_market_summary": "이 응답은 LS증권/Gemini 키 없이 화면과 JSON 연동을 확인하기 위한 더미 데이터입니다.",
        "disclaimer": "이 결과는 더미 데이터 기반 예시이며 매수·매도 추천이 아닙니다.",
    }


def _compact_json(data: Any, max_chars: int = MAX_FALLBACK_JSON_CHARS) -> str:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... (truncated)"


def _pick_first(item: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _is_missing_env_value(value: str) -> bool:
    lowered = value.strip().lower()
    return (
        not lowered
        or lowered.startswith("your_")
        or "여기에" in lowered
        or "넣으세요" in lowered
    )


def _get_gemini_model() -> str:
    model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
    if model in DEPRECATED_GEMINI_MODELS:
        print(
            f"{model} 모델을 현재 API에서 찾지 못할 수 있어 "
            f"{DEFAULT_GEMINI_MODEL}로 대체합니다."
        )
        return DEFAULT_GEMINI_MODEL
    return model or DEFAULT_GEMINI_MODEL


def _get_gemini_models() -> list[str]:
    models = [_get_gemini_model()]
    fallback_value = os.getenv("GEMINI_FALLBACK_MODELS", "").strip()
    fallback_models = (
        [model.strip() for model in fallback_value.split(",") if model.strip()]
        if fallback_value
        else DEFAULT_GEMINI_FALLBACK_MODELS
    )

    for model in fallback_models:
        if model not in models:
            models.append(model)
    return models


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "y", "on"}


def _find_news_items(data: Any) -> list[dict[str, Any]]:
    """Find likely news item dictionaries in a flexible API response."""
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]

    if not isinstance(data, dict):
        return []

    candidate_keys = (
        "news",
        "items",
        "data",
        "result",
        "results",
        "list",
        "articles",
        "body",
        "output",
        "OutBlock",
        "OutBlock1",
    )
    for key in candidate_keys:
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            nested_items = _find_news_items(value)
            if nested_items:
                return nested_items

    for value in data.values():
        nested_items = _find_news_items(value)
        if nested_items:
            return nested_items

    return []


def _has_no_news_data_message(data: Any) -> bool:
    text = _compact_json(data, max_chars=2000) if not isinstance(data, str) else data
    return any(message in text for message in NO_NEWS_DATA_MESSAGES)


def _find_first_news_identifier(data: Any) -> dict[str, str]:
    if isinstance(data, list):
        for item in data:
            identifier = _find_first_news_identifier(item)
            if identifier:
                return identifier
        return {}

    if not isinstance(data, dict):
        return {}

    single_id = _pick_first(
        data,
        (
            "hot_code",
            "sNewsno",
            "news_no",
            "newsNo",
            "newsno",
            "nws_no",
            "nwsNo",
            "id",
        ),
    )
    if single_id:
        return {"sNewsno": single_id}

    news_date = _pick_first(data, ("n_date", "news_date", "date"))
    news_time = _pick_first(data, ("n_time", "news_time", "time"))
    news_seq = _pick_first(data, ("seq", "n_seq", "news_seq"))
    if news_date and news_time and news_seq:
        return {
            "n_date": news_date,
            "n_time": news_time,
            "seq": news_seq,
        }

    for value in data.values():
        identifier = _find_first_news_identifier(value)
        if identifier:
            return identifier

    return {}


def _format_news_data(api_json: Any) -> str:
    if _has_no_news_data_message(api_json):
        return ""

    title_block = api_json.get("t3102OutBlock2") if isinstance(api_json, dict) else None
    body_block = api_json.get("t3102OutBlock1") if isinstance(api_json, dict) else None
    stock_block = api_json.get("t3102OutBlock") if isinstance(api_json, dict) else None

    if isinstance(body_block, list):
        body = "\n".join(str(item.get("sBody", "")) for item in body_block if isinstance(item, dict))
        body = _clean_news_text(body)

        title = ""
        if isinstance(title_block, dict):
            title = str(title_block.get("sTitle", "")).strip()
        elif isinstance(title_block, list) and title_block and isinstance(title_block[0], dict):
            title = str(title_block[0].get("sTitle", "")).strip()

        stock_codes = []
        if isinstance(stock_block, list):
            stock_codes = [
                str(item.get("sJongcode", "")).strip()
                for item in stock_block
                if isinstance(item, dict) and str(item.get("sJongcode", "")).strip()
            ]

        parts = ["[LS증권 API 뉴스본문 데이터]"]
        if title:
            parts.append(f"제목: {title}")
        if stock_codes:
            parts.append(f"관련 종목코드: {', '.join(stock_codes)}")
        if body:
            parts.append(f"본문:\n{body}")
        if len(parts) > 1:
            return "\n".join(parts)

    items = _find_news_items(api_json)
    formatted_items: list[str] = []

    for index, item in enumerate(items[:30], start=1):
        title = _pick_first(
            item,
            ("title", "headline", "news_title", "newsTitle", "subject", "tit", "hts_kor_isnm"),
        )
        date = _pick_first(
            item,
            ("date", "datetime", "published_at", "publishDate", "news_date", "newsDate", "time"),
        )
        body = _pick_first(
            item,
            (
                "body",
                "content",
                "summary",
                "description",
                "news_body",
                "newsBody",
                "article",
                "text",
            ),
        )

        if title or date or body:
            formatted_items.append(
                f"{index}. 날짜: {date or '알 수 없음'}\n"
                f"   제목: {title or '제목 없음'}\n"
                f"   내용: {body or '본문/요약 없음'}"
            )

    if formatted_items:
        return "[LS증권 API 최신 뉴스 데이터]\n" + "\n\n".join(formatted_items)

    print("LS증권 뉴스 응답 구조가 예상과 달라 원본 JSON 일부를 사용합니다.")
    fallback_text = "[LS증권 API 원본 응답 일부]\n" + _compact_json(api_json)
    if _has_no_news_data_message(fallback_text):
        return ""
    return fallback_text


def _clean_news_text(text: str) -> str:
    cleaned = html.unescape(text)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = cleaned.replace("\r", "\n")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()


def fetch_ls_access_token(app_key: str, app_secret: str) -> str:
    token_url = os.getenv("LS_TOKEN_URL", LS_DEFAULT_TOKEN_URL).strip() or LS_DEFAULT_TOKEN_URL
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecretkey": app_secret,
        "scope": "oob",
    }

    try:
        response = requests.post(
            token_url,
            headers=headers,
            data=data,
            timeout=LS_REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            print(
                "LS증권 접근토큰 발급 실패: "
                f"HTTP {response.status_code} - {response.text[:500]}"
            )
            return ""

        token_json = response.json()
        access_token = str(token_json.get("access_token", "")).strip()
        if not access_token:
            print("LS증권 접근토큰 응답에 access_token이 없습니다.")
            print(_compact_json(token_json, max_chars=1000))
            return ""

        expires_in = token_json.get("expires_in") or token_json.get("expire_in")
        if expires_in:
            print(f"LS증권 접근토큰을 발급받았습니다. expires_in={expires_in}")
        else:
            print("LS증권 접근토큰을 발급받았습니다.")
        return access_token

    except requests.Timeout:
        print(f"LS증권 접근토큰 발급 시간이 {LS_REQUEST_TIMEOUT}초를 초과했습니다.")
    except requests.RequestException as exc:
        print(f"LS증권 접근토큰 발급 중 네트워크 오류가 발생했습니다: {exc}")
    except ValueError:
        print("LS증권 접근토큰 응답이 JSON 형식이 아닙니다.")
    except Exception as exc:
        print(f"LS증권 접근토큰 처리 중 예상치 못한 오류가 발생했습니다: {exc}")

    return ""


def request_ls_api(
    access_token: str,
    api_url: str,
    tr_code: str,
    payload: dict[str, Any],
    description: str,
) -> dict[str, Any] | None:
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {access_token}",
        "tr_cd": tr_code,
        "tr_cont": "N",
        "tr_cont_key": "",
        "mac_address": "",
    }

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=LS_REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            print(f"{description} 실패: HTTP {response.status_code} - {response.text[:500]}")
            return None

        try:
            return response.json()
        except ValueError:
            print(f"{description} 응답이 JSON 형식이 아닙니다.")
            print(response.text[:MAX_FALLBACK_JSON_CHARS])
            return None

    except requests.Timeout:
        print(f"{description} 시간이 {LS_REQUEST_TIMEOUT}초를 초과했습니다.")
    except requests.RequestException as exc:
        print(f"{description} 중 네트워크 오류가 발생했습니다: {exc}")
    except Exception as exc:
        print(f"{description} 중 예상치 못한 오류가 발생했습니다: {exc}")

    return None


def build_t3102_input_block() -> dict[str, str]:
    """
    Build t3102 input block from known LS/eBEST news identifier variants.

    Some LS documents expose a single news identifier as sNewsno or hot_code.
    Older eBEST-style guides may describe the same lookup as n_date + n_time + seq.
    Keep the payload easy to adjust while the exact portal spec is being confirmed.
    """
    news_no = os.getenv("LS_NEWS_NO", "").strip()
    hot_code = os.getenv("LS_NEWS_HOT_CODE", "").strip()
    news_date = os.getenv("LS_NEWS_DATE", "").strip()
    news_time = os.getenv("LS_NEWS_TIME", "").strip()
    news_seq = os.getenv("LS_NEWS_SEQ", "").strip()

    if not _is_missing_env_value(hot_code):
        return {"sNewsno": hot_code}

    if not _is_missing_env_value(news_no):
        return {"sNewsno": news_no}

    if not any(_is_missing_env_value(value) for value in (news_date, news_time, news_seq)):
        return {
            "n_date": news_date,
            "n_time": news_time,
            "seq": news_seq,
        }

    return {}


async def _fetch_latest_news_input_block_from_websocket(access_token: str) -> dict[str, str]:
    try:
        import websockets
    except ImportError:
        print("websockets 패키지가 설치되어 있지 않습니다. pip install websockets 후 다시 실행하세요.")
        return {}

    ws_url = os.getenv("LS_NEWS_WS_URL", LS_DEFAULT_NEWS_WS_URL).strip() or LS_DEFAULT_NEWS_WS_URL
    tr_key = os.getenv("LS_NEWS_WS_TR_KEY", LS_DEFAULT_NEWS_WS_TR_KEY).strip() or LS_DEFAULT_NEWS_WS_TR_KEY
    timeout = int(os.getenv("LS_NEWS_WS_TIMEOUT", "30"))
    ssl_context = ssl.create_default_context()
    if not _env_flag("LS_NEWS_WS_SSL_VERIFY", default=False):
        ssl_context = ssl._create_unverified_context()

    subscribe_message = {
        "header": {
            "token": access_token,
            "tr_type": "3",
        },
        "body": {
            "tr_cd": "NWS",
            "tr_key": tr_key,
        },
    }

    try:
        async with websockets.connect(
            ws_url,
            ssl=ssl_context,
            ping_interval=20,
            close_timeout=5,
        ) as websocket:
            await websocket.send(json.dumps(subscribe_message, ensure_ascii=False))
            print(f"LS 뉴스 웹소켓 NWS 구독을 시작했습니다. tr_key={tr_key}, timeout={timeout}s")

            while True:
                raw_message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                try:
                    message = json.loads(raw_message)
                except json.JSONDecodeError:
                    print(f"LS 뉴스 웹소켓에서 JSON이 아닌 메시지를 받았습니다: {raw_message[:300]}")
                    continue

                body = message.get("body", {}) if isinstance(message, dict) else {}
                if not isinstance(body, dict):
                    continue

                realkey = str(body.get("realkey", "")).strip()
                title = str(body.get("title", "")).strip()
                if realkey:
                    if title:
                        print(f"최신 뉴스 제목을 수신했습니다: {title}")
                    print(f"NWS realkey를 t3102 뉴스번호로 사용합니다: {realkey}")
                    return {"sNewsno": realkey}

                header = message.get("header", {}) if isinstance(message, dict) else {}
                rsp_msg = body.get("rsp_msg") or message.get("rsp_msg") or header.get("rsp_msg")
                if rsp_msg:
                    print(f"LS 뉴스 웹소켓 메시지: {rsp_msg}")

    except asyncio.TimeoutError:
        print(f"{timeout}초 동안 신규 NWS 뉴스 패킷이 없어 뉴스번호를 가져오지 못했습니다.")
    except Exception as exc:
        print(f"LS 뉴스 웹소켓 처리 중 오류가 발생했습니다: {exc}")

    return {}


def fetch_latest_news_input_block(access_token: str) -> dict[str, str]:
    return asyncio.run(_fetch_latest_news_input_block_from_websocket(access_token))


def fetch_ls_news_body(access_token: str, news_api_url: str, input_block: dict[str, str]) -> str:
    payload = {
        "t3102InBlock": input_block,
    }

    api_json = request_ls_api(
        access_token=access_token,
        api_url=news_api_url,
        tr_code=LS_NEWS_TR_CODE,
        payload=payload,
        description="LS증권 뉴스 본문 API(t3102) 호출",
    )
    if not api_json:
        return ""

    news_data = _format_news_data(api_json)
    if not news_data.strip():
        print("t3102 본문 응답에 실제 뉴스 본문이 없어 다음 뉴스 패킷을 기다립니다.")
        return ""

    return news_data


def fetch_ls_news() -> str:
    """
    Fetch recent news from LS Securities API.

    t3102는 뉴스 식별자(hot_code/sNewsno 또는 n_date+n_time+seq)로 뉴스 본문을 조회하는 TR입니다.
    최신 뉴스 목록 TR(t3101/t3104 등)이 연결되기 전에는 .env에 테스트할 뉴스 식별자를 넣어 사용하세요.
    """
    app_key = os.getenv("LS_APP_KEY", "").strip()
    app_secret = os.getenv("LS_APP_SECRET", "").strip()
    access_token = os.getenv("LS_ACCESS_TOKEN", "").strip()
    news_api_url = os.getenv("LS_NEWS_API_URL", LS_DEFAULT_NEWS_API_URL).strip()

    if _is_missing_env_value(app_key) or _is_missing_env_value(app_secret):
        print("LS_APP_KEY 또는 LS_APP_SECRET이 비어 있어 샘플 뉴스 데이터를 사용합니다.")
        return ""

    if not access_token:
        access_token = fetch_ls_access_token(app_key, app_secret)

    if not access_token:
        print("LS증권 접근토큰을 준비하지 못해 샘플 뉴스 데이터를 사용합니다.")
        return ""

    manual_input_block = build_t3102_input_block()
    if manual_input_block:
        return fetch_ls_news_body(access_token, news_api_url, manual_input_block)

    max_attempts = int(os.getenv("LS_NEWS_MAX_ATTEMPTS", "5"))
    for attempt in range(1, max_attempts + 1):
        print(f"본문 조회 가능한 최신 뉴스 패킷을 찾는 중입니다. attempt={attempt}/{max_attempts}")
        input_block = fetch_latest_news_input_block(access_token)
        if not input_block:
            continue

        news_data = fetch_ls_news_body(access_token, news_api_url, input_block)
        if news_data.strip():
            return news_data

    print("본문 조회 가능한 뉴스 패킷을 찾지 못했습니다.")

    return ""


def build_prompt(news_data: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    # 실제 서비스에서는 Gemini가 반환한 종목코드를 LS증권 종목 마스터 데이터로 검증해야 합니다.
    return f"""
당신은 한국 주식 시장 전문 AI 애널리스트입니다.
사용자는 LS증권 API를 활용하여 수집한 최신 뉴스 데이터를 바탕으로 투자 참고용 종목 추천 서비스를 만들고 있습니다.

당신의 역할은 아래 뉴스 데이터를 분석하여,
현재 시장에서 뉴스 모멘텀이 강한 한국 상장 주식 5개를 추천하는 것입니다.

중요한 규칙:
- 반드시 제공된 뉴스 데이터에 근거해서만 분석하세요.
- 뉴스 데이터에 근거가 부족한 종목은 추천하지 마세요.
- 종목명과 종목코드는 가능한 한 정확하게 작성하세요.
- 잘 모르는 종목코드는 빈 문자열("")로 두세요.
- 실제 서비스에서는 Gemini가 반환한 종목코드를 LS증권 종목 마스터 데이터로 검증해야 합니다.
- 투자 추천이 아니라 "뉴스 기반 투자 참고 분석" 관점으로 작성하세요.
- 과장된 표현을 피하고, 리스크를 반드시 포함하세요.
- 추천 결과는 반드시 5개 종목이어야 합니다.
- analysis_date는 "{today}"를 사용하세요.
- 출력은 반드시 JSON 객체 하나만 반환하세요.
- 마크다운, 설명문, 코드블록, 주석은 절대 포함하지 마세요.

분석 절차:
1. 뉴스에서 핵심 키워드를 추출합니다.
2. 반복적으로 등장하는 산업/테마를 파악합니다.
3. 해당 테마와 직접적으로 연결된 상장사를 찾습니다.
4. 단기 모멘텀 가능성이 높은 종목을 5개 선정합니다.
5. 각 종목별 추천 근거와 위험 요인을 작성합니다.

[최신 뉴스 데이터]
{news_data}

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "analysis_date": "{today}",
  "top_themes": [
    "핵심 테마 1",
    "핵심 테마 2",
    "핵심 테마 3"
  ],
  "recommendations": [
    {{
      "rank": 1,
      "stock_name": "종목명",
      "stock_code": "종목코드 또는 모르면 빈 문자열",
      "market": "KOSPI 또는 KOSDAQ 또는 모르면 빈 문자열",
      "theme": "관련 테마",
      "reason": "뉴스 기반 추천 이유",
      "news_evidence": "추천 근거가 된 뉴스 내용 요약",
      "expected_momentum": "예상되는 단기 모멘텀",
      "risk": "주의해야 할 위험 요소",
      "confidence": "상/중/하"
    }},
    {{
      "rank": 2,
      "stock_name": "종목명",
      "stock_code": "종목코드 또는 모르면 빈 문자열",
      "market": "KOSPI 또는 KOSDAQ 또는 모르면 빈 문자열",
      "theme": "관련 테마",
      "reason": "뉴스 기반 추천 이유",
      "news_evidence": "추천 근거가 된 뉴스 내용 요약",
      "expected_momentum": "예상되는 단기 모멘텀",
      "risk": "주의해야 할 위험 요소",
      "confidence": "상/중/하"
    }},
    {{
      "rank": 3,
      "stock_name": "종목명",
      "stock_code": "종목코드 또는 모르면 빈 문자열",
      "market": "KOSPI 또는 KOSDAQ 또는 모르면 빈 문자열",
      "theme": "관련 테마",
      "reason": "뉴스 기반 추천 이유",
      "news_evidence": "추천 근거가 된 뉴스 내용 요약",
      "expected_momentum": "예상되는 단기 모멘텀",
      "risk": "주의해야 할 위험 요소",
      "confidence": "상/중/하"
    }},
    {{
      "rank": 4,
      "stock_name": "종목명",
      "stock_code": "종목코드 또는 모르면 빈 문자열",
      "market": "KOSPI 또는 KOSDAQ 또는 모르면 빈 문자열",
      "theme": "관련 테마",
      "reason": "뉴스 기반 추천 이유",
      "news_evidence": "추천 근거가 된 뉴스 내용 요약",
      "expected_momentum": "예상되는 단기 모멘텀",
      "risk": "주의해야 할 위험 요소",
      "confidence": "상/중/하"
    }},
    {{
      "rank": 5,
      "stock_name": "종목명",
      "stock_code": "종목코드 또는 모르면 빈 문자열",
      "market": "KOSPI 또는 KOSDAQ 또는 모르면 빈 문자열",
      "theme": "관련 테마",
      "reason": "뉴스 기반 추천 이유",
      "news_evidence": "추천 근거가 된 뉴스 내용 요약",
      "expected_momentum": "예상되는 단기 모멘텀",
      "risk": "주의해야 할 위험 요소",
      "confidence": "상/중/하"
    }}
  ],
  "overall_market_summary": "뉴스 데이터를 바탕으로 본 전체 시장 분위기 요약",
  "disclaimer": "이 결과는 뉴스 기반 AI 분석이며 매수·매도 추천이 아닙니다. 실제 투자 전 재무제표, 공시, 수급, 차트, 리스크를 반드시 확인해야 합니다."
}}
""".strip()


def _strip_json_code_block(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _extract_json_object(text: str) -> str:
    cleaned = _strip_json_code_block(text)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        return cleaned[start : end + 1]
    return cleaned


def analyze_news_with_gemini(news_data: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if _is_missing_env_value(api_key):
        print(
            "Gemini API Key가 없습니다. .env 파일 또는 환경변수에 "
            "GEMINI_API_KEY를 설정한 뒤 다시 실행해 주세요."
        )
        sys.exit(1)

    prompt = build_prompt(news_data)
    client = genai.Client(api_key=api_key)

    max_retries = int(os.getenv("GEMINI_MAX_RETRIES", "3"))
    response = None
    last_error: Exception | None = None

    for gemini_model in _get_gemini_models():
        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=gemini_model,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "temperature": 0.2,
                    },
                )
                break
            except Exception as exc:
                last_error = exc
                error_text = str(exc)
                if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                    print(
                        "Gemini API 사용량 한도에 도달했습니다. 잠시 후 다시 실행하거나, "
                        "Google AI Studio/API 콘솔에서 결제 또는 quota 설정을 확인해 주세요."
                    )
                    print(f"사용 모델: {gemini_model}")
                    sys.exit(1)

                if "503" in error_text or "UNAVAILABLE" in error_text:
                    wait_seconds = min(2**attempt, 10)
                    print(
                        f"Gemini 모델이 혼잡합니다. model={gemini_model}, "
                        f"attempt={attempt}/{max_retries}, {wait_seconds}초 후 재시도합니다."
                    )
                    time.sleep(wait_seconds)
                    continue

                print(f"Gemini API 호출 중 오류가 발생했습니다: {exc}")
                sys.exit(1)

        if response is not None:
            break

        print(f"{gemini_model} 모델 재시도가 실패해 다음 fallback 모델을 시도합니다.")

    if response is None:
        print(f"Gemini API 호출을 완료하지 못했습니다: {last_error}")
        sys.exit(1)

    raw_text = getattr(response, "text", None)
    if not raw_text or not raw_text.strip():
        print("Gemini 응답이 비어 있습니다.")
        sys.exit(1)

    cleaned_text = _extract_json_object(raw_text)

    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError as exc:
        print("Gemini 응답을 JSON으로 파싱하지 못했습니다.")
        print(f"오류: {exc}")
        print("\n[Gemini 원본 응답]")
        print(raw_text)
        sys.exit(1)


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env", override=True)

    if _env_flag("USE_DUMMY_AI", default=False):
        result = get_dummy_analysis_result()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    news_data = fetch_ls_news()
    if not news_data.strip():
        if not _env_flag("USE_SAMPLE_NEWS", default=False):
            print(
                "LS증권 실제 뉴스 데이터를 가져오지 못해 종료합니다. "
                "샘플 뉴스로 Gemini 흐름만 테스트하려면 .env에 USE_SAMPLE_NEWS=true를 설정하세요."
            )
            sys.exit(1)
        print("USE_SAMPLE_NEWS=true 설정에 따라 샘플 뉴스 데이터를 사용합니다.")
        news_data = get_sample_news_data()

    result = analyze_news_with_gemini(news_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
