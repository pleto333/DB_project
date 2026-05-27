from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_FALLBACK_MODELS = ["gemini-2.0-flash", "gemini-2.5-flash-lite"]
DEPRECATED_GEMINI_MODELS = {"gemini-1.5-flash", "models/gemini-1.5-flash"}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LS_DEFAULT_TOKEN_URL = "https://openapi.ls-sec.co.kr:8080/oauth2/token"
LS_DEFAULT_NEWS_API_URL = "https://openapi.ls-sec.co.kr:8080/stock/investinfo"
LS_DEFAULT_NEWS_WS_URL = "wss://openapi.ls-sec.co.kr:9443/websocket"
LS_DEFAULT_NEWS_WS_TR_KEY = "NWS001"
LS_NEWS_TR_CODE = "t3102"
LS_DEFAULT_STOCK_API_URL = "https://openapi.ls-sec.co.kr:8080/stock/chart"
LS_CHART_TR_CODE = "t8413"
LS_DEFAULT_STOCK_MARKET_URL = "https://openapi.ls-sec.co.kr:8080/stock/market-data"
LS_CURRENT_PRICE_TR_CODE = "t1102"
LS_REQUEST_TIMEOUT = 10
MAX_FALLBACK_JSON_CHARS = 4000
NO_NEWS_DATA_MESSAGES = (
    "해당자료가 없습니다",
    "해당 자료가 없습니다",
    "다시 조회 바랍니다",
)


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "y", "on"}


def is_missing_env_value(value: str) -> bool:
    lowered = value.strip().lower()
    return (
        not lowered
        or lowered.startswith("your_")
        or "여기에" in lowered
        or "넣으세요" in lowered
    )


def get_gemini_model() -> str:
    model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
    if model in DEPRECATED_GEMINI_MODELS:
        print(f"{model} 모델을 {DEFAULT_GEMINI_MODEL}로 대체합니다.")
        return DEFAULT_GEMINI_MODEL
    return model or DEFAULT_GEMINI_MODEL


def get_gemini_models() -> list[str]:
    models = [get_gemini_model()]
    fallback_value = os.getenv("GEMINI_FALLBACK_MODELS", "").strip()
    fallback_models = (
        [m.strip() for m in fallback_value.split(",") if m.strip()]
        if fallback_value
        else DEFAULT_GEMINI_FALLBACK_MODELS
    )
    for model in fallback_models:
        if model not in models:
            models.append(model)
    return models
