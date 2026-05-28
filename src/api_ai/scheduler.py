from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import ssl
import sys
from datetime import datetime
from typing import Any

from .config import (
    DEFAULT_GEMINI_MODEL,
    LS_DEFAULT_NEWS_WS_URL,
    get_gemini_model,
    get_project_root,
)
from .gemini import GeminiRateLimitError, analyze_news_with_gemini, get_dummy_analysis_result, get_sample_news_data
from .ls_api import fetch_ls_access_token, fetch_ls_news

# 실시간 지수 데이터 저장소
market_indices: dict[str, Any] = {
    "kospi": {"value": None, "drate": None, "sign": None, "change": None, "updated_at": None},
    "kosdaq": {"value": None, "drate": None, "sign": None, "change": None, "updated_at": None},
}


def _save_news_to_db(news_data: str, proj_root) -> None:
    """뉴스 텍스트를 파싱해 news_articles 테이블에 개별 기사로 저장."""
    if not news_data or news_data in ("auto", "rate_limit_fallback"):
        return

    try:
        if str(proj_root) not in sys.path:
            sys.path.insert(0, str(proj_root))
        from src.db.database import save_news_article
    except Exception as exc:
        print(f"[뉴스저장] DB import 오류: {exc}")
        return

    articles: list[dict] = []

    # 번호 형식 뉴스 목록 파싱:
    #   [LS증권 API 최신 뉴스 데이터] 또는 [샘플 뉴스 데이터]
    #   "N. 날짜: DATE\n   제목: TITLE\n   내용: BODY"
    if re.search(r'\d+\.\s+날짜:', news_data):
        blocks = re.split(r'\n\d+\.\s+날짜:', news_data)
        for block in blocks[1:]:
            lines = block.split('\n')
            date_str = lines[0].strip() if lines else ''
            title_m = re.search(r'제목:\s*(.+)', block)
            body_m = re.search(r'내용:\s*([\s\S]+)', block)
            title = title_m.group(1).strip() if title_m else ''
            body = body_m.group(1).strip() if body_m else ''
            if not title or title == '제목 없음':
                continue
            articles.append({
                'title': title[:300],
                'summary': body[:2000] if body and body != '본문/요약 없음' else None,
                'published_at': date_str if date_str and date_str not in ('알 수 없음', '-') else None,
            })

    # 단일 기사 본문 형식: [LS증권 API 뉴스본문 데이터]
    elif "[LS증권 API 뉴스본문 데이터]" in news_data:
        title_m = re.search(r'제목:\s*(.+)', news_data)
        body_m = re.search(r'본문:\n([\s\S]+)', news_data)
        title = title_m.group(1).strip() if title_m else ''
        body = body_m.group(1).strip() if body_m else ''
        if title:
            articles.append({
                'title': title[:300],
                'summary': body[:2000] if body else None,
                'published_at': None,
            })

    saved = 0
    for art in articles:
        # URL은 제목 해시로 생성 (LS API는 기사 URL을 제공하지 않음)
        url = f"ls://news/{hashlib.md5(art['title'].encode('utf-8')).hexdigest()}"
        try:
            save_news_article(
                title=art['title'],
                url=url,
                summary=art.get('summary'),
                publisher='LS증권',
                source='ls_securities',
                published_at=art.get('published_at'),
            )
            saved += 1
        except Exception:
            pass  # 중복 등 개별 오류 무시
    if saved:
        print(f"[뉴스저장] {saved}건 news_articles 저장 완료.")


def save_analysis_to_db(result: dict[str, Any], news_data: str = "") -> int | None:
    try:
        proj_root = get_project_root()
        if str(proj_root) not in sys.path:
            sys.path.insert(0, str(proj_root))
        from src.db.database import add_stock, save_llm_analysis, save_stock_recommendation

        model_name = get_gemini_model()
        analysis_id = save_llm_analysis(
            model_name=model_name,
            input_summary=(news_data[:500] if news_data else "auto"),
            response=result,
        )

        for rec in result.get("recommendations", []):
            stock_code = str(rec.get("stock_code", "")).strip()
            stock_name = str(rec.get("stock_name", "")).strip()
            market_raw = str(rec.get("market", "KOSPI")).strip().upper()
            rank_no = int(rec.get("rank", 0))
            reason = str(rec.get("reason", "")).strip()
            confidence_str = str(rec.get("confidence", "중")).strip()

            if not stock_name:
                continue
            # 종목코드가 없거나 숫자 코드가 아니면 저장하지 않음 (ETF/테마 추상 항목 차단)
            if not stock_code or not stock_code.isdigit():
                print(f"[분석저장] rank {rank_no} '{stock_name}' — 유효한 종목코드 없음, 건너뜀")
                continue

            market_enum = market_raw if market_raw in ("KOSPI", "KOSDAQ", "NASDAQ", "NYSE") else "OTHER"
            stock_id = add_stock(stock_code, stock_name, market_enum)

            confidence_map = {"상": 0.8, "중": 0.5, "하": 0.2}
            confidence_value = confidence_map.get(confidence_str, 0.5)
            recommendation = "BUY" if confidence_str == "상" else "WATCH"

            save_stock_recommendation(
                analysis_id=analysis_id,
                stock_id=stock_id,
                rank_no=rank_no,
                recommendation=recommendation,
                reason=reason,
                confidence=confidence_value,
            )

        print(f"DB 저장 완료: analysis_id={analysis_id}")
        # news_articles 테이블에 개별 뉴스 기사 저장
        _save_news_to_db(news_data, proj_root)
        return analysis_id
    except Exception as exc:
        print(f"DB 저장 중 오류 (분석 결과는 정상 반환): {exc}")
        return None


_KR_STOCK_KEYWORDS = (
    "코스피", "코스닥", "삼성", "현대", "SK", "LG", "카카오", "네이버", "셀트리온",
    "한화", "포스코", "기아", "005930", "000660", "KOSPI", "KOSDAQ",
    "수주", "매출", "영업이익", "HBM", "반도체", "조선", "바이오",
)


def _is_korean_stock_news(news_data: str) -> bool:
    """LS 뉴스가 한국 주식 관련 내용인지 간단히 판별."""
    return any(kw in news_data for kw in _KR_STOCK_KEYWORDS)


async def run_scheduled_analysis() -> None:
    """서버 시작 시 즉시 한 번 실행 후 10분마다 반복. 실패 시 1분 후 재시도 (최대 3회)."""
    loop = asyncio.get_event_loop()
    retry_count = 0
    MAX_RETRIES = 3

    while True:
        try:
            print("[스케줄러] AI 분석 시작...")
            news_data = await loop.run_in_executor(None, fetch_ls_news)

            if not news_data.strip():
                print("[스케줄러] 뉴스 데이터 없음. 샘플 데이터 사용.")
                news_data = get_sample_news_data()
            elif not _is_korean_stock_news(news_data):
                print("[스케줄러] 한국 주식 관련 뉴스 없음. 샘플 데이터 사용.")
                news_data = get_sample_news_data()

            result = await loop.run_in_executor(None, analyze_news_with_gemini, news_data)
            save_analysis_to_db(result, news_data)
            print("[스케줄러] 분석 완료. 다음 실행까지 10분 대기.")
            retry_count = 0
            await asyncio.sleep(600)

        except GeminiRateLimitError as exc:
            # Gemini 사용량 한도: 더미 데이터로 DB 저장 후 1시간 대기
            print(f"[스케줄러] {exc} 더미 데이터로 대체 저장 후 1시간 대기.")
            try:
                save_analysis_to_db(get_dummy_analysis_result(), "rate_limit_fallback")
            except Exception as save_exc:
                print(f"[스케줄러] 더미 데이터 저장 실패: {save_exc}")
            await asyncio.sleep(3600)

        except Exception as exc:
            retry_count += 1
            if retry_count <= MAX_RETRIES:
                wait = 60 * retry_count  # 1분 → 2분 → 3분
                print(f"[스케줄러] 오류 (시도 {retry_count}/{MAX_RETRIES}): {exc}. {wait}초 후 재시도.")
            else:
                wait = 600
                retry_count = 0
                print(f"[스케줄러] 최대 재시도 초과: {exc}. 10분 후 재시도.")
            await asyncio.sleep(wait)


async def _subscribe_market_index(access_token: str, tr_key: str, market: str) -> None:
    """IJ_ WebSocket TR을 구독해 실시간 지수 데이터를 market_indices에 저장."""
    try:
        import websockets
    except ImportError:
        print("[지수] websockets 패키지가 없습니다. pip install websockets")
        return

    ws_url = os.getenv("LS_NEWS_WS_URL", LS_DEFAULT_NEWS_WS_URL).strip() or LS_DEFAULT_NEWS_WS_URL
    ssl_context = ssl._create_unverified_context()
    subscribe_message = {
        "header": {"token": access_token, "tr_type": "3"},
        "body": {"tr_cd": "IJ_", "tr_key": tr_key},
    }

    while True:
        try:
            async with websockets.connect(ws_url, ssl=ssl_context, ping_interval=20, close_timeout=5) as ws:
                await ws.send(json.dumps(subscribe_message))
                print(f"[지수] IJ_ 구독 시작. market={market}, tr_key={tr_key}")
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    body = msg.get("body", {}) if isinstance(msg, dict) else {}
                    if not isinstance(body, dict):
                        continue
                    jisu = body.get("jisu")
                    if not jisu:
                        continue
                    market_indices[market] = {
                        "value": str(jisu).strip(),
                        "drate": str(body.get("drate", "0")).strip(),
                        "sign": str(body.get("sign", "3")).strip(),
                        "change": str(body.get("change", "0")).strip(),
                        "updated_at": datetime.now().isoformat(),
                    }
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"[지수] {market} WebSocket 오류: {exc}. 10초 후 재연결...")
            await asyncio.sleep(10)


async def run_market_indices() -> None:
    """KOSPI(001) + KOSDAQ(101) IJ_ WebSocket 구독을 시작."""
    from .config import is_missing_env_value

    app_key = os.getenv("LS_APP_KEY", "").strip()
    app_secret = os.getenv("LS_APP_SECRET", "").strip()
    if is_missing_env_value(app_key) or is_missing_env_value(app_secret):
        print("[지수] LS_APP_KEY/SECRET 미설정. 지수 실시간 데이터를 건너뜁니다.")
        return

    access_token = os.getenv("LS_ACCESS_TOKEN", "").strip()
    if not access_token:
        loop = asyncio.get_event_loop()
        access_token = await loop.run_in_executor(None, fetch_ls_access_token, app_key, app_secret)

    if not access_token:
        print("[지수] 토큰 발급 실패. 지수 실시간 데이터를 건너뜁니다.")
        return

    await asyncio.gather(
        _subscribe_market_index(access_token, "001", "kospi"),
        _subscribe_market_index(access_token, "101", "kosdaq"),
    )
