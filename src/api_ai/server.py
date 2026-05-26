from __future__ import annotations

import asyncio
import hashlib
import os
import sys
import time
from contextlib import asynccontextmanager
from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
except ImportError as exc:
    raise RuntimeError("pip install fastapi uvicorn 명령으로 설치해 주세요.") from exc

from .config import get_project_root
from .gemini import analyze_news_with_gemini, get_dummy_analysis_result, get_sample_news_data
from .ls_api import fetch_ls_access_token, fetch_ls_news, fetch_stock_daily_prices
from .scheduler import market_indices, run_market_indices, run_scheduled_analysis, save_analysis_to_db


class AnalyzeRequest(BaseModel):
    news_data: str | None = Field(default=None)
    use_sample_news: bool = Field(default=False)
    use_dummy_ai: bool = Field(default=False)


class PortfolioRequest(BaseModel):
    user_id: str | int
    stock_code: str
    stock_name: str | None = Field(default=None)


class PortfolioDeleteRequest(BaseModel):
    user_id: str | int
    stock_code: str


class RegisterRequest(BaseModel):
    id: str
    password: str
    email: str
    nickname: str


class LoginRequest(BaseModel):
    id: str
    password: str


def create_web_app():

    @asynccontextmanager
    async def lifespan(app):
        task1 = asyncio.create_task(run_scheduled_analysis())
        task2 = asyncio.create_task(run_market_indices())
        yield
        task1.cancel()
        task2.cancel()
        for task in (task1, task2):
            try:
                await task
            except asyncio.CancelledError:
                pass

    app = FastAPI(
        title="LS Securities News Gemini Analyzer",
        description="LS증권 뉴스 기반 Gemini AI 종목 추천 API",
        version="1.0.0",
        lifespan=lifespan,
    )

    cors_origins_text = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
    )
    cors_origins = [o.strip() for o in cors_origins_text.split(",") if o.strip()]
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/")
    def root() -> dict[str, str]:
        return {"message": "LS Securities News Gemini Analyzer API", "health": "/health", "docs": "/docs"}

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/analyze")
    def analyze(request: AnalyzeRequest) -> dict[str, Any]:
        try:
            if request.use_dummy_ai:
                result = get_dummy_analysis_result()
                save_analysis_to_db(result)
                return result
            selected_news_data = (request.news_data or "").strip()
            if not selected_news_data:
                selected_news_data = get_sample_news_data() if request.use_sample_news else fetch_ls_news()
            if not selected_news_data.strip():
                raise HTTPException(status_code=400, detail="뉴스 데이터를 가져오지 못했습니다.")
            result = analyze_news_with_gemini(selected_news_data)
            save_analysis_to_db(result, selected_news_data)
            return result
        except HTTPException:
            raise
        except SystemExit as exc:
            raise HTTPException(status_code=500, detail=f"분석 처리 중 종료: {exc}") from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"분석 처리 중 오류: {exc}") from exc

    @app.get("/recommendations/latest")
    def get_latest_recommendations() -> dict[str, Any]:
        try:
            proj_root = get_project_root()
            if str(proj_root) not in sys.path:
                sys.path.insert(0, str(proj_root))
            from src.db.database import get_latest_analysis_json
            result = get_latest_analysis_json()
            if not result:
                raise HTTPException(status_code=404, detail="저장된 분석 결과가 없습니다. /analyze 를 먼저 호출해 주세요.")
            return result
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"DB 조회 중 오류: {exc}") from exc

    @app.get("/market/indices")
    async def get_market_indices() -> dict[str, Any]:
        return market_indices

    @app.get("/portfolio")
    def get_portfolio(user_id: str) -> dict[str, Any]:
        try:
            proj_root = get_project_root()
            if str(proj_root) not in sys.path:
                sys.path.insert(0, str(proj_root))
            from src.db.database import get_portfolio_by_user
            return {"items": get_portfolio_by_user(int(user_id))}
        except Exception as exc:
            raise HTTPException(status_code=500, detail={"message": f"포트폴리오 조회 실패: {exc}"})

    @app.post("/portfolio")
    def add_to_portfolio(request: PortfolioRequest) -> dict[str, str]:
        try:
            proj_root = get_project_root()
            if str(proj_root) not in sys.path:
                sys.path.insert(0, str(proj_root))
            from src.db.database import add_portfolio_item
            add_portfolio_item(int(request.user_id), request.stock_code, request.stock_name or request.stock_code)
            return {"status": "ok"}
        except Exception as exc:
            raise HTTPException(status_code=500, detail={"message": f"포트폴리오 추가 실패: {exc}"})

    @app.delete("/portfolio")
    def remove_from_portfolio(request: PortfolioDeleteRequest) -> dict[str, str]:
        try:
            proj_root = get_project_root()
            if str(proj_root) not in sys.path:
                sys.path.insert(0, str(proj_root))
            from src.db.database import remove_portfolio_item
            remove_portfolio_item(int(request.user_id), request.stock_code)
            return {"status": "ok"}
        except Exception as exc:
            raise HTTPException(status_code=500, detail={"message": f"포트폴리오 제거 실패: {exc}"})

    @app.post("/register")
    def register(request: RegisterRequest) -> dict[str, Any]:
        try:
            proj_root = get_project_root()
            if str(proj_root) not in sys.path:
                sys.path.insert(0, str(proj_root))
            from src.db.database import add_user
            password_hash = hashlib.sha256(request.password.encode()).hexdigest()
            user_id = add_user(username=request.id, email=request.email, password_hash=password_hash)
            return {"status": "ok", "user_id": user_id, "message": "회원가입이 완료되었습니다."}
        except Exception as exc:
            error_msg = str(exc)
            if "Duplicate entry" in error_msg:
                raise HTTPException(status_code=409, detail={"message": "이미 사용 중인 아이디 또는 이메일입니다."})
            raise HTTPException(status_code=500, detail={"message": f"회원가입에 실패했습니다: {exc}"})

    @app.post("/login")
    def login(request: LoginRequest) -> dict[str, Any]:
        try:
            proj_root = get_project_root()
            if str(proj_root) not in sys.path:
                sys.path.insert(0, str(proj_root))
            from src.db.database import get_user_by_username
            user = get_user_by_username(request.id)
            if not user:
                raise HTTPException(status_code=401, detail={"message": "아이디 또는 비밀번호가 올바르지 않습니다."})
            password_hash = hashlib.sha256(request.password.encode()).hexdigest()
            if user["password_hash"] != password_hash:
                raise HTTPException(status_code=401, detail={"message": "아이디 또는 비밀번호가 올바르지 않습니다."})
            return {
                "status": "ok",
                "user_id": str(user["user_id"]),
                "username": user["username"],
                "email": user["email"],
            }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail={"message": f"로그인 오류: {exc}"})

    _price_cache: dict[str, tuple[float, list[float]]] = {}
    _PRICE_CACHE_TTL = 300

    @app.get("/stocks/price")
    async def get_stock_prices(codes: str) -> dict[str, Any]:
        code_list = [c.strip() for c in codes.split(",") if c.strip()]
        if not code_list:
            return {}

        access_token = os.getenv("LS_ACCESS_TOKEN", "").strip()
        if not access_token:
            from .config import is_missing_env_value
            app_key = os.getenv("LS_APP_KEY", "").strip()
            app_secret = os.getenv("LS_APP_SECRET", "").strip()
            if not is_missing_env_value(app_key) and not is_missing_env_value(app_secret):
                loop = asyncio.get_event_loop()
                access_token = await loop.run_in_executor(None, fetch_ls_access_token, app_key, app_secret)

        result: dict[str, list[float]] = {}
        now = time.time()
        loop = asyncio.get_event_loop()
        first_api_call = True
        for code in code_list:
            cached = _price_cache.get(code)
            if cached and now - cached[0] < _PRICE_CACHE_TTL:
                result[code] = cached[1]
                continue
            prices: list[float] = []
            if access_token:
                if not first_api_call:
                    await asyncio.sleep(1.2)
                first_api_call = False
                try:
                    prices = await loop.run_in_executor(None, fetch_stock_daily_prices, access_token, code, 10)
                except Exception:
                    prices = []
            if prices:
                _price_cache[code] = (now, prices)
            result[code] = prices
        return result

    return app


def run_web_server() -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("pip install uvicorn 명령으로 설치해 주세요.") from exc

    host = os.getenv("WEB_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port_text = os.getenv("WEB_PORT", "8000").strip() or "8000"
    try:
        port = int(port_text)
    except ValueError:
        port = 8000

    from .server import create_web_app as _create
    uvicorn.run(_create(), host=host, port=port)
