from __future__ import annotations

import asyncio
import datetime
import html
import json
import os
import re
import ssl
import threading
import time
from typing import Any

import requests

from .config import (
    LS_CHART_TR_CODE,
    LS_CURRENT_PRICE_TR_CODE,
    LS_DEFAULT_NEWS_API_URL,
    LS_DEFAULT_STOCK_MARKET_URL,
    LS_DEFAULT_NEWS_WS_TR_KEY,
    LS_DEFAULT_NEWS_WS_URL,
    LS_DEFAULT_STOCK_API_URL,
    LS_DEFAULT_TOKEN_URL,
    LS_NEWS_TR_CODE,
    LS_REQUEST_TIMEOUT,
    MAX_FALLBACK_JSON_CHARS,
    NO_NEWS_DATA_MESSAGES,
    env_flag,
    is_missing_env_value,
)


# ── t8413 전역 rate limiter (0.3s 간격 강제) ───────────────────────────────
_t8413_lock = threading.Lock()
_t8413_last_call: float = 0.0
_T8413_INTERVAL = 0.3  # 초

def _t8413_throttle() -> None:
    """t8413 호출 전 반드시 실행 — 전 스레드에 걸쳐 0.3s 간격 보장."""
    global _t8413_last_call
    with _t8413_lock:
        now = time.time()
        wait = _T8413_INTERVAL - (now - _t8413_last_call)
        if wait > 0:
            time.sleep(wait)
        _t8413_last_call = time.time()


def compact_json(data: Any, max_chars: int = MAX_FALLBACK_JSON_CHARS) -> str:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... (truncated)"


def pick_first(item: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _find_news_items(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        return []
    candidate_keys = ("news", "items", "data", "result", "results", "list",
                      "articles", "body", "output", "OutBlock", "OutBlock1")
    for key in candidate_keys:
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            nested = _find_news_items(value)
            if nested:
                return nested
    for value in data.values():
        nested = _find_news_items(value)
        if nested:
            return nested
    return []


def _has_no_news_data_message(data: Any) -> bool:
    text = compact_json(data, max_chars=2000) if not isinstance(data, str) else data
    return any(msg in text for msg in NO_NEWS_DATA_MESSAGES)


def _find_first_news_identifier(data: Any) -> dict[str, str]:
    if isinstance(data, list):
        for item in data:
            identifier = _find_first_news_identifier(item)
            if identifier:
                return identifier
        return {}
    if not isinstance(data, dict):
        return {}
    single_id = pick_first(data, ("hot_code", "sNewsno", "news_no", "newsNo", "newsno", "nws_no", "nwsNo", "id"))
    if single_id:
        return {"sNewsno": single_id}
    news_date = pick_first(data, ("n_date", "news_date", "date"))
    news_time = pick_first(data, ("n_time", "news_time", "time"))
    news_seq = pick_first(data, ("seq", "n_seq", "news_seq"))
    if news_date and news_time and news_seq:
        return {"n_date": news_date, "n_time": news_time, "seq": news_seq}
    for value in data.values():
        identifier = _find_first_news_identifier(value)
        if identifier:
            return identifier
    return {}


def _fix_mojibake(text: str) -> str:
    """UTF-8 바이트를 Latin-1로 잘못 읽은 mojibake 복구 시도.
    â€™ / Ã± 같은 패턴이 보이면 latin-1 → utf-8 재디코딩."""
    # 대체 문자(U+FFFD) 우선 제거
    text = text.replace('�', '')
    # mojibake 징표: â€, Ã, Â 등 Latin-1 상위 바이트 연속 패턴
    if re.search(r'[âãÃÂ]\S', text):
        try:
            text = text.encode('latin-1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return text


def _clean_news_text(text: str) -> str:
    cleaned = _fix_mojibake(text)
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # t3102OutBlock 블록명 접두사 제거 (LS API 이진 응답 파싱 시 블록명이 필드값에 섞이는 문제)
    cleaned = re.sub(r'^t3102OutBlock\w*\s*', '', cleaned, flags=re.IGNORECASE)
    # C0 제어문자 제거 (탭·LF·CR 제외)
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', cleaned)
    # LS API 고정폭 이진 잔재: 14자리 날짜코드 + 언론사명 패턴 제거 (예: 20260528111805한국경제)
    cleaned = re.sub(r'\d{14}[가-힣A-Za-z0-9]*', '', cleaned)
    # LS API 이진 프로토콜 잔재 패턴 제거:
    #   - " ^XX" 캐럿+대문자 패턴 (예: ^AH, ^v가, ^x0)
    #   - " _XX" 언더스코어+알파뉴메릭 패턴 (예: _AH, _飭)
    #   - " C LIMIT" / " js" 스타일 임의 ASCII 문자열
    cleaned = re.sub(r'\s+\^[\w\W]{0,30}$', '', cleaned)           # title 끝 ^xxx 이진 패턴
    cleaned = re.sub(r'(\s+\^[^\s가-힣]+)', ' ', cleaned)           # 본문 중간 ^xxx 패턴
    cleaned = re.sub(r'\s+_[A-Z가-힣]{1,10}(\s|$)', ' ', cleaned)  # _AH, _飭 패턴
    cleaned = re.sub(r'\s+[A-Z]{1}\s+[A-Z]{2,}\s+\d.*$', '', cleaned)  # "C LIMIT 4..." 트레일링
    # 이진 잔재: CJK 통합 한자 연속 2자 이상 (한국 뉴스 본문에 등장하는 한자 시퀀스 = 이진 잔재)
    cleaned = re.sub(r'[一-鿿]{2,}', '', cleaned)
    # 이진 잔재: 한글 음절 사이에 끼어든 단독 CJK 한자
    cleaned = re.sub(r'(?<=[가-힣])\s*[一-鿿]\s*(?=[가-힣])', '', cleaned)
    # 이진 잔재: 단독 한글 자모 (ㄱ-ㅎ, ㅏ-ㅣ) 가 이진 패턴 뒤에 나타나는 경우
    cleaned = re.sub(r'[ㄱ-ㆎ][一-鿿]*', '', cleaned)
    # 이진 잔재: 로마 숫자 단일 문자 (Ⅰ~ⅿ, U+2160-U+2188)
    cleaned = re.sub(r'[Ⅰ-ↈ]', '', cleaned)
    # 이진 잔재: 키릴(러시아어) 문자 — 한국 뉴스에 등장하면 100% 이진 프로토콜 잔재
    cleaned = re.sub(r'[Ѐ-ԯ]', '', cleaned)
    # 이진 잔재: 단독 CJK 문자 (공백이나 한글 인접 시 모두 제거)
    cleaned = re.sub(r'(?<=\s)[一-鿿](?=\s)', ' ', cleaned)
    cleaned = re.sub(r'(?<=[가-힣])[一-鿿]', '', cleaned)
    cleaned = re.sub(r'[一-鿿](?=[가-힣])', '', cleaned)
    # 이진 잔재: LS API 레코드 구분자 ◆◇◈ (문장 중간에서만 제거, 줄 시작 불릿은 유지)
    cleaned = re.sub(r'(?<=[가-힣A-Za-z0-9])\s*[◆◇◈]\s*(?=[가-힣A-Za-z0-9])', ' ', cleaned)
    cleaned = re.sub(r'[◆◇◈]', '', cleaned)  # 나머지 잔재 제거
    # 이진 잔재: 화살표 블록 중 LS API 잔재로만 쓰이는 것만 제거 (← → ↑ ↓ 등)
    # ●▶▷▲△▼▽ 등 뉴스 불릿/기호는 유지
    cleaned = re.sub(r'[←↑↓↔↕↖↗↘↙⇒⇔⇒⇐⇑⇓⇕]', '', cleaned)
    # 사진 캡션 제거: "/사진=..." 또는 "[사진=...]" 형식
    cleaned = re.sub(r'[/\[]사진=[^\]\n]*[\]\n]?', '', cleaned)
    cleaned = re.sub(r'\[?사진\s*=\s*[^\]\n]*\]?', '', cleaned)
    # 기사 출처 표기 제거: "[언론사/기자명 기자(이메일)]" 형식
    cleaned = re.sub(r'\[[^\]]{0,40}/[^\]]{0,40}\s*기자[^\]]*\]', '', cleaned)
    # 하이퍼링크 안내 푸터 제거 (파이낸셜뉴스 등): "→ ..." 스타일
    cleaned = re.sub(r'→[^\n]{0,100}\n?', '', cleaned)
    # 언론사 저작권 고지 제거
    cleaned = re.sub(r'※\s*저작권자[^\n]*\n?', '', cleaned)
    # 기자 이메일 주소 제거
    cleaned = re.sub(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', '', cleaned)
    cleaned = cleaned.replace("\r", "\n")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()


def _clean_title(text: str) -> str:
    """제목 전용 클리닝 — 이진 잔재 이후 텍스트를 잘라냄."""
    cleaned = _clean_news_text(text)
    # 제목에 남은 고정폭 이진 잔재 트레일링 완전 제거:
    # 캐럿·언더스코어·대괄호 등 이진 시그니처 이후 전체 제거
    cleaned = re.sub(r'\s*[\^_\|\\{}\[\]~`]+.*$', '', cleaned)
    # " - GARBAGE" 또는 " SO GARBAGE" 스타일 (대문자 단어 2개+ 이진 패턴)
    cleaned = re.sub(r'\s+-\s*[^\s가-힣a-zA-Z0-9"\'%·\-,\.·’“”…]+.*$', '', cleaned)
    return cleaned.strip()


def _format_news_data(api_json: Any) -> str:
    if _has_no_news_data_message(api_json):
        return ""

    title_block = api_json.get("t3102OutBlock2") if isinstance(api_json, dict) else None
    body_block = api_json.get("t3102OutBlock1") if isinstance(api_json, dict) else None
    stock_block = api_json.get("t3102OutBlock") if isinstance(api_json, dict) else None

    if isinstance(body_block, list):
        body = "\n".join(str(item.get("sBody", "")) for item in body_block if isinstance(item, dict))
        body = _clean_news_text(body)

        # HTML/CSS 응답 감지: LS API가 오류 HTML 페이지를 반환한 경우 무시
        _html_signals = ("font-size:", "line-height:", "font-family:", "@media", "body,td,", "border:0px")
        if any(sig in body for sig in _html_signals):
            print("[뉴스파싱] HTML 오류 응답 감지 — 해당 뉴스 패킷 무시.")
            return ""

        title = ""
        if isinstance(title_block, dict):
            title = _clean_title(str(title_block.get("sTitle", "")))
        elif isinstance(title_block, list) and title_block and isinstance(title_block[0], dict):
            title = _clean_title(str(title_block[0].get("sTitle", "")))

        # 제목이 없거나 너무 짧으면(5자 미만) 본문에서 의미 있는 첫 줄을 대체 제목으로 사용
        # 사진 캡션·짧은 줄·기호로 시작하는 줄은 건너뜀
        _meaningful_title = re.sub(r'[^\w가-힣]', '', title)  # 한글·영숫자만 세기
        if len(_meaningful_title) < 5 and body:
            for line in body.split('\n'):
                line = line.strip()
                # 한글이 5자 이상 있는 줄만 제목으로 채택
                if (len(re.sub(r'[^가-힣]', '', line)) >= 5
                        and not line.startswith('/')
                        and not line.startswith('[')
                        and not line.startswith('※')
                        and not line.startswith('→')):
                    title = line[:80]
                    break

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
        title = pick_first(item, ("title", "headline", "news_title", "newsTitle", "subject", "tit", "hts_kor_isnm"))
        date = pick_first(item, ("date", "datetime", "published_at", "publishDate", "news_date", "newsDate", "time"))
        body = pick_first(item, ("body", "content", "summary", "description", "news_body", "newsBody", "article", "text"))
        if title or date or body:
            formatted_items.append(
                f"{index}. 날짜: {date or '알 수 없음'}\n"
                f"   제목: {title or '제목 없음'}\n"
                f"   내용: {body or '본문/요약 없음'}"
            )

    if formatted_items:
        return "[LS증권 API 최신 뉴스 데이터]\n" + "\n\n".join(formatted_items)

    print("LS증권 뉴스 응답 구조가 예상과 달라 원본 JSON 일부를 사용합니다.")
    fallback_text = "[LS증권 API 원본 응답 일부]\n" + compact_json(api_json)
    if _has_no_news_data_message(fallback_text):
        return ""
    return fallback_text


def fetch_ls_access_token(app_key: str, app_secret: str) -> str:
    token_url = os.getenv("LS_TOKEN_URL", LS_DEFAULT_TOKEN_URL).strip() or LS_DEFAULT_TOKEN_URL
    try:
        response = requests.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials", "appkey": app_key, "appsecretkey": app_secret, "scope": "oob"},
            timeout=LS_REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            print(f"LS증권 접근토큰 발급 실패: HTTP {response.status_code} - {response.text[:500]}")
            return ""
        token_json = response.json()
        access_token = str(token_json.get("access_token", "")).strip()
        if not access_token:
            print("LS증권 접근토큰 응답에 access_token이 없습니다.")
            return ""
        expires_in = token_json.get("expires_in") or token_json.get("expire_in")
        print(f"LS증권 접근토큰을 발급받았습니다.{f' expires_in={expires_in}' if expires_in else ''}")
        return access_token
    except requests.Timeout:
        print(f"LS증권 접근토큰 발급 시간이 {LS_REQUEST_TIMEOUT}초를 초과했습니다.")
    except requests.RequestException as exc:
        print(f"LS증권 접근토큰 발급 중 네트워크 오류: {exc}")
    except Exception as exc:
        print(f"LS증권 접근토큰 처리 중 오류: {exc}")
    return ""


def request_ls_api(access_token: str, api_url: str, tr_code: str, payload: dict[str, Any], description: str) -> dict[str, Any] | None:
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {access_token}",
        "tr_cd": tr_code, "tr_cont": "N", "tr_cont_key": "", "mac_address": "",
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=LS_REQUEST_TIMEOUT)
        if response.status_code != 200:
            print(f"{description} 실패: HTTP {response.status_code} - {response.text[:500]}")
            return None
        return response.json()
    except requests.Timeout:
        print(f"{description} 시간이 {LS_REQUEST_TIMEOUT}초를 초과했습니다.")
    except requests.RequestException as exc:
        print(f"{description} 중 네트워크 오류: {exc}")
    except Exception as exc:
        print(f"{description} 중 오류: {exc}")
    return None


def build_t3102_input_block() -> dict[str, str]:
    news_no = os.getenv("LS_NEWS_NO", "").strip()
    hot_code = os.getenv("LS_NEWS_HOT_CODE", "").strip()
    news_date = os.getenv("LS_NEWS_DATE", "").strip()
    news_time = os.getenv("LS_NEWS_TIME", "").strip()
    news_seq = os.getenv("LS_NEWS_SEQ", "").strip()

    if not is_missing_env_value(hot_code):
        return {"sNewsno": hot_code}
    if not is_missing_env_value(news_no):
        return {"sNewsno": news_no}
    if not any(is_missing_env_value(v) for v in (news_date, news_time, news_seq)):
        return {"n_date": news_date, "n_time": news_time, "seq": news_seq}
    return {}


async def _fetch_news_keys_from_websocket(access_token: str, max_collect: int = 5) -> list[dict[str, str]]:
    """WebSocket NWS 구독에서 최대 max_collect개의 뉴스 realkey를 수집."""
    try:
        import websockets
    except ImportError:
        print("websockets 패키지가 없습니다. pip install websockets")
        return []

    ws_url = os.getenv("LS_NEWS_WS_URL", LS_DEFAULT_NEWS_WS_URL).strip() or LS_DEFAULT_NEWS_WS_URL
    tr_key = os.getenv("LS_NEWS_WS_TR_KEY", LS_DEFAULT_NEWS_WS_TR_KEY).strip() or LS_DEFAULT_NEWS_WS_TR_KEY
    timeout = int(os.getenv("LS_NEWS_WS_TIMEOUT", "30"))
    ssl_context = ssl.create_default_context()
    if not env_flag("LS_NEWS_WS_SSL_VERIFY", default=False):
        ssl_context = ssl._create_unverified_context()

    subscribe_message = {
        "header": {"token": access_token, "tr_type": "3"},
        "body": {"tr_cd": "NWS", "tr_key": tr_key},
    }
    collected: list[dict[str, str]] = []
    seen: set[str] = set()
    try:
        async with websockets.connect(ws_url, ssl=ssl_context, ping_interval=20, close_timeout=5) as ws:
            await ws.send(json.dumps(subscribe_message, ensure_ascii=False))
            print(f"LS NWS 구독 시작. 최대 {max_collect}건 수집 (timeout={timeout}s)")
            while len(collected) < max_collect:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
                except asyncio.TimeoutError:
                    break  # 타임아웃 → 지금까지 수집한 것으로 종료
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                body = message.get("body", {}) if isinstance(message, dict) else {}
                if not isinstance(body, dict):
                    continue
                realkey = str(body.get("realkey", "")).strip()
                title = str(body.get("title", "")).strip()
                if realkey and realkey not in seen:
                    seen.add(realkey)
                    collected.append({"sNewsno": realkey})
                    print(f"  [{len(collected)}/{max_collect}] {title or realkey}")
                rsp_msg = body.get("rsp_msg") or message.get("rsp_msg") or message.get("header", {}).get("rsp_msg")
                if rsp_msg:
                    print(f"LS NWS 메시지: {rsp_msg}")
    except Exception as exc:
        print(f"LS 뉴스 웹소켓 처리 중 오류: {exc}")
    if not collected:
        print(f"{timeout}초 동안 신규 NWS 뉴스 패킷이 없었습니다.")
    return collected


def fetch_latest_news_input_block(access_token: str) -> dict[str, str]:
    keys = asyncio.run(_fetch_news_keys_from_websocket(access_token, max_collect=1))
    return keys[0] if keys else {}


def _articles_to_combined(articles: list[str]) -> str:
    """여러 [LS증권 API 뉴스본문 데이터] 블록을 번호형 목록으로 합쳐 반환."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    if len(articles) == 1:
        return articles[0]
    items = []
    for art in articles:
        title_m = re.search(r'제목:\s*(.+)', art)
        body_m = re.search(r'본문:\n([\s\S]+)', art)
        title = title_m.group(1).strip() if title_m else ''
        body = body_m.group(1).strip() if body_m else ''
        if title:
            items.append((title, body))
    if not items:
        return articles[0]
    lines = ["[LS증권 API 최신 뉴스 데이터]"]
    for i, (title, body) in enumerate(items, 1):
        lines.append(f"{i}. 날짜: {today}")
        lines.append(f"   제목: {title}")
        lines.append(f"   내용: {body[:800] if body else '본문 없음'}")
        lines.append("")
    return "\n".join(lines)


def fetch_ls_news_body(access_token: str, news_api_url: str, input_block: dict[str, str]) -> str:
    api_json = request_ls_api(
        access_token=access_token,
        api_url=news_api_url,
        tr_code=LS_NEWS_TR_CODE,
        payload={"t3102InBlock": input_block},
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
    app_key = os.getenv("LS_APP_KEY", "").strip()
    app_secret = os.getenv("LS_APP_SECRET", "").strip()
    access_token = os.getenv("LS_ACCESS_TOKEN", "").strip()
    news_api_url = os.getenv("LS_NEWS_API_URL", LS_DEFAULT_NEWS_API_URL).strip()

    if is_missing_env_value(app_key) or is_missing_env_value(app_secret):
        print("LS_APP_KEY 또는 LS_APP_SECRET이 비어 있어 LS증권 뉴스 API 호출을 건너뜁니다.")
        return ""

    if not access_token:
        access_token = fetch_ls_access_token(app_key, app_secret)
    if not access_token:
        print("LS증권 접근토큰을 준비하지 못해 샘플 뉴스 데이터를 사용합니다.")
        return ""

    manual_input_block = build_t3102_input_block()
    if manual_input_block:
        return fetch_ls_news_body(access_token, news_api_url, manual_input_block)

    max_collect = int(os.getenv("LS_NEWS_MAX_COLLECT", "5"))
    print(f"NWS WebSocket에서 최대 {max_collect}건 뉴스 수집 시작...")
    input_blocks = asyncio.run(_fetch_news_keys_from_websocket(access_token, max_collect))

    articles: list[str] = []
    for input_block in input_blocks:
        news_data = fetch_ls_news_body(access_token, news_api_url, input_block)
        if news_data.strip():
            articles.append(news_data)

    if not articles:
        print("본문 조회 가능한 뉴스 패킷을 찾지 못했습니다.")
        return ""

    print(f"뉴스 {len(articles)}건 수집 완료.")
    return _articles_to_combined(articles)


def fetch_global_indices() -> dict[str, Any]:
    try:
        import yfinance as yf
    except ImportError:
        print("yfinance 패키지가 없습니다. pip install yfinance")
        return {}

    symbols = {
        "KOSPI": "^KS11",
        "KOSDAQ": "^KQ11",
        "NASDAQ": "^IXIC",
        "S&P500": "^GSPC",
        "DOW": "^DJI",
        "닛케이": "^N225",
        "WTI": "CL=F",
        "금": "GC=F",
        "환율(USD)": "USDKRW=X",
    }
    result: dict[str, Any] = {}
    for name, symbol in symbols.items():
        try:
            fi = yf.Ticker(symbol).fast_info
            price = fi.last_price
            prev = fi.previous_close
            if price and prev:
                result[name] = {"price": round(float(price), 2), "change": round((price - prev) / prev * 100, 2)}
        except Exception:
            pass
    return result


def fetch_stock_daily_prices(access_token: str, stock_code: str, days: int = 10) -> list[float]:
    _t8413_throttle()  # 전역 0.3s 간격 적용
    stock_api_url = os.getenv("LS_STOCK_API_URL", LS_DEFAULT_STOCK_API_URL).strip() or LS_DEFAULT_STOCK_API_URL
    payload = {
        "t8413InBlock": {
            "shcode": stock_code,
            "gubun": "2",
            "qrycnt": days,
            "sdate": "19000101",
            "edate": "99991231",
            "cts_date": "",
            "comp_yn": "N",
            "sujung": "Y",
        }
    }
    api_json = request_ls_api(
        access_token=access_token,
        api_url=stock_api_url,
        tr_code=LS_CHART_TR_CODE,
        payload=payload,
        description=f"t8413 일봉({stock_code})",
    )
    if not api_json:
        return []
    out_block = api_json.get("t8413OutBlock1", [])
    if not isinstance(out_block, list):
        return []
    prices: list[float] = []
    for item in reversed(out_block):
        if not isinstance(item, dict):
            continue
        close = item.get("close")
        if close is None:
            continue
        try:
            val = float(str(close).replace(",", ""))
            if val > 0:   # 0원 데이터(비거래일/미래 날짜) 제외
                prices.append(val)
        except (ValueError, TypeError):
            pass
    return prices


def is_market_open() -> bool:
    """한국 주식 시장 개장 여부 (09:00~15:30 KST, 평일)."""
    now = datetime.datetime.now()
    if now.weekday() >= 5:  # 토(5), 일(6)
        return False
    market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close


def fetch_stock_current_price(access_token: str, stock_code: str) -> dict[str, Any]:
    """장중: t1102 현재가 조회. 장외: t8413 최근 종가 fallback."""
    # 한국 종목코드는 6자리 — AI가 앞 0을 빠뜨린 경우 보정
    stock_code = str(stock_code).strip().zfill(6)

    def _from_daily() -> dict[str, Any]:
        # days=5: 오늘 장 마감 직후 당일 데이터가 없어도 2개 확보 가능
        prices = fetch_stock_daily_prices(access_token, stock_code, days=5)
        prices = [p for p in prices if p > 0]
        if len(prices) >= 2:
            price, prev = prices[-1], prices[-2]
            change = round(price - prev, 0)
            drate = round((price - prev) / prev * 100, 2) if prev else 0.0
            return {"code": stock_code, "price": price, "change": change, "drate": drate, "is_realtime": False}
        if len(prices) == 1:
            # 데이터 1건: 가격은 반환하되 drate=None으로 "데이터 부족" 표시
            return {"code": stock_code, "price": prices[0], "change": None, "drate": None, "is_realtime": False}
        return {"code": stock_code, "price": None, "change": None, "drate": None, "is_realtime": False}

    # t1102는 장중·장외 모두 최종 체결가를 반환 — 항상 먼저 시도
    # 장외에도 당일 종가를 돌려주므로 is_market_open() 체크 불필요
    # 장중: t1102 현재가
    market_url = os.getenv("LS_STOCK_MARKET_URL", LS_DEFAULT_STOCK_MARKET_URL).strip() or LS_DEFAULT_STOCK_MARKET_URL
    payload = {"t1102InBlock": {"shcode": stock_code}}
    api_json = request_ls_api(
        access_token=access_token,
        api_url=market_url,
        tr_code=LS_CURRENT_PRICE_TR_CODE,
        payload=payload,
        description=f"t1102 현재가({stock_code})",
    )

    if not api_json:
        return _from_daily()

    out = api_json.get("t1102OutBlock", {})
    if not isinstance(out, dict):
        return _from_daily()

    try:
        price = float(str(out.get("price") or 0).replace(",", ""))
        change = float(str(out.get("change") or 0).replace(",", ""))
        sign = str(out.get("sign", "3"))
        # sign: 1=상한, 2=상승, 3=보합, 4=하락, 5=하한
        if sign in ("4", "5"):
            change = -abs(change)
        # drate는 t1102 응답에 없음 → change에서 역산
        # price - change = 전일 종가, drate = change / 전일종가 * 100
        prev_close = price - change
        drate: float | None = round(change / prev_close * 100, 2) if prev_close > 0 and change != 0 else None
        if price <= 0:
            return _from_daily()
        return {"code": stock_code, "price": price, "change": change, "drate": drate, "is_realtime": True}
    except (ValueError, TypeError):
        return _from_daily()
