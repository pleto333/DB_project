from __future__ import annotations

import asyncio
import json
import os
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
from .gemini import analyze_news_with_gemini, get_sample_news_data
from .ls_api import fetch_ls_access_token, fetch_ls_news

# 실시간 지수 데이터 저장소
market_indices: dict[str, Any] = {
    "kospi": {"value": None, "drate": None, "sign": None, "change": None, "updated_at": None},
    "kosdaq": {"value": None, "drate": None, "sign": None, "change": None, "updated_at": None},
}


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
            if not stock_code:
                stock_code = f"TBD_{rank_no}"

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
        return analysis_id
    except Exception as exc:
        print(f"DB 저장 중 오류 (분석 결과는 정상 반환): {exc}")
        return None


async def run_scheduled_analysis() -> None:
    """서버 시작 시 즉시 한 번 실행 후 10분마다 반복."""
    loop = asyncio.get_event_loop()
    while True:
        try:
            print("[스케줄러] AI 분석 시작...")
            news_data = await loop.run_in_executor(None, fetch_ls_news)
            if not news_data.strip():
                news_data = get_sample_news_data()
            result = await loop.run_in_executor(None, analyze_news_with_gemini, news_data)
            save_analysis_to_db(result, news_data)
            print("[스케줄러] 분석 완료. 다음 실행까지 10분 대기.")
        except (Exception, SystemExit) as exc:
            print(f"[스케줄러] 오류: {exc}. 10분 후 재시도.")
        await asyncio.sleep(600)


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
