from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from mysql.connector import Error

from src.db.database import (
    get_all_analysis_news_articles_json,
    get_all_recommendations_json,
    get_analysis_news_articles_json,
    get_analyses_json,
    get_latest_analysis_id,
    get_latest_recommendations_json,
    get_recommendations_json,
)
from src.db.demo_data import demo_analyses, demo_news_articles, demo_recommendations


BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"

app = FastAPI(
    title="Stock News Recommendation API",
    description="뉴스 기반 LLM 주식 종목 추천 서비스 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=PUBLIC_DIR), name="static")


def _json_safe(value: Any) -> Any:
    """Convert DB values into JSON-friendly values."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    return value


def _with_source(payload: dict[str, Any], data_source: str) -> dict[str, Any]:
    result = dict(payload)
    result["data_source"] = data_source
    return result


def _with_demo_source(payload: dict[str, Any], exc: Error) -> dict[str, Any]:
    result = _with_source(payload, "demo")
    result["db_error"] = str(exc)
    return result


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "stock-news-recommendation-api"}


@app.get("/dashboard")
def dashboard() -> FileResponse:
    return FileResponse(PUBLIC_DIR / "index.html")


@app.get("/api/recommendations/latest")
def latest_recommendations() -> dict[str, Any]:
    """Return the latest LLM stock recommendation result."""
    try:
        return _with_source(_json_safe(get_latest_recommendations_json()), "database")
    except Error as exc:
        return _with_demo_source(demo_recommendations(), exc)


@app.get("/api/analyses")
def analyses() -> dict[str, Any]:
    """Return saved LLM analysis batches."""
    try:
        return _with_source(_json_safe(get_analyses_json()), "database")
    except Error as exc:
        return _with_demo_source(demo_analyses(), exc)


@app.get("/api/recommendations")
def all_recommendations() -> dict[str, Any]:
    """Return all stock recommendation results."""
    try:
        return _with_source(_json_safe(get_all_recommendations_json()), "database")
    except Error as exc:
        return _with_demo_source(demo_recommendations(), exc)


@app.get("/api/analyses/news")
def all_analysis_news() -> dict[str, Any]:
    """Return news articles used by all LLM analyses."""
    try:
        return _with_source(_json_safe(get_all_analysis_news_articles_json()), "database")
    except Error as exc:
        return _with_demo_source(demo_news_articles(), exc)


@app.get("/api/analyses/latest/news")
def latest_analysis_news() -> dict[str, Any]:
    """Return the news articles used by the latest LLM analysis."""
    try:
        analysis_id = get_latest_analysis_id()
        if analysis_id is None:
            return _with_source({"analysis_id": None, "news_articles": []}, "database")
        return _with_source(_json_safe(get_analysis_news_articles_json(analysis_id)), "database")
    except Error as exc:
        return _with_demo_source(demo_news_articles(), exc)


@app.get("/api/analyses/{analysis_id}/recommendations")
def recommendations_by_analysis(analysis_id: int) -> dict[str, Any]:
    """Return stock recommendations for one LLM analysis result."""
    try:
        return _with_source(_json_safe(get_recommendations_json(analysis_id)), "database")
    except Error as exc:
        return _with_demo_source(demo_recommendations(analysis_id), exc)


@app.get("/api/analyses/{analysis_id}/news")
def news_by_analysis(analysis_id: int) -> dict[str, Any]:
    """Return news articles used by one LLM analysis result."""
    try:
        return _with_source(_json_safe(get_analysis_news_articles_json(analysis_id)), "database")
    except Error as exc:
        return _with_demo_source(demo_news_articles(analysis_id), exc)
