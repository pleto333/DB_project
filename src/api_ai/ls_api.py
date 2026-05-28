from __future__ import annotations

import asyncio
import datetime
import html
import json
import os
import re
import ssl
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


def _clean_news_text(text: str) -> str:
    cleaned = html.unescape(text)
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

        # 제목이 없으면 본문 첫 문장을 제목으로 대체 (저장 누락 방지)
        if not title and body:
            first_line = body.split('\n')[0].strip()
            title = first_line[:80] if first_line else ""

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


async def _fetch_latest_news_input_block_from_websocket(access_token: str) -> dict[str, str]:
    try:
        import websockets
    except ImportError:
        print("websockets 패키지가 없습니다. pip install websockets")
        return {}

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
    try:
        async with websockets.connect(ws_url, ssl=ssl_context, ping_interval=20, close_timeout=5) as ws:
            await ws.send(json.dumps(subscribe_message, ensure_ascii=False))
            print(f"LS 뉴스 웹소켓 NWS 구독을 시작했습니다. tr_key={tr_key}, timeout={timeout}s")
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
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
                rsp_msg = body.get("rsp_msg") or message.get("rsp_msg") or message.get("header", {}).get("rsp_msg")
                if rsp_msg:
                    print(f"LS 뉴스 웹소켓 메시지: {rsp_msg}")
    except asyncio.TimeoutError:
        print(f"{timeout}초 동안 신규 NWS 뉴스 패킷이 없어 뉴스번호를 가져오지 못했습니다.")
    except Exception as exc:
        print(f"LS 뉴스 웹소켓 처리 중 오류: {exc}")
    return {}


def fetch_latest_news_input_block(access_token: str) -> dict[str, str]:
    return asyncio.run(_fetch_latest_news_input_block_from_websocket(access_token))


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

    def _from_daily() -> dict[str, Any]:
        prices = fetch_stock_daily_prices(access_token, stock_code, days=2)
        # 0 이하 값은 무효 데이터이므로 제거 (이미 fetch에서 필터되지만 방어적으로 재확인)
        prices = [p for p in prices if p > 0]
        if len(prices) >= 2:
            price, prev = prices[-1], prices[-2]
            change = round(price - prev, 0)
            drate = round((price - prev) / prev * 100, 2) if prev else 0.0
            return {"code": stock_code, "price": price, "change": change, "drate": drate, "is_realtime": False}
        if len(prices) == 1:
            return {"code": stock_code, "price": prices[0], "change": 0.0, "drate": 0.0, "is_realtime": False}
        return {"code": stock_code, "price": None, "change": None, "drate": None, "is_realtime": False}

    if not is_market_open():
        return _from_daily()

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
        drate = float(str(out.get("drate") or 0).replace(",", "").replace("%", ""))
        sign = str(out.get("sign", "3"))
        # sign: 1=상한, 2=상승, 3=보합, 4=하락, 5=하한
        if sign in ("4", "5"):
            drate = -abs(drate)
            change = -abs(change)
        if price <= 0:
            return _from_daily()
        return {"code": stock_code, "price": price, "change": change, "drate": drate, "is_realtime": True}
    except (ValueError, TypeError):
        return _from_daily()
