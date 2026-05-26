"""
LS Securities news -> Gemini analysis end-to-end.

uvicorn 실행:
    cd <project_root>
    python3 -m uvicorn src.api_ai.AI:app --host 0.0.0.0 --port 8080

CLI 실행:
    python3 -m src.api_ai.AI
"""

from __future__ import annotations

import json
import sys

from .config import PROJECT_ROOT, env_flag
from .gemini import analyze_news_with_gemini, get_dummy_analysis_result, get_sample_news_data
from .ls_api import fetch_ls_news
from .scheduler import save_analysis_to_db
from .server import create_web_app

# ASGI 진입점 (uvicorn src.api_ai.AI:app)
app = create_web_app()


def main() -> None:
    if env_flag("RUN_WEB_SERVER", default=False):
        from .server import run_web_server
        run_web_server()
        return

    if env_flag("USE_DUMMY_AI", default=False):
        result = get_dummy_analysis_result()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    news_data = fetch_ls_news()
    if not news_data.strip():
        if not env_flag("USE_SAMPLE_NEWS", default=True):
            print("LS증권 실제 뉴스 데이터를 가져오지 못했습니다. USE_SAMPLE_NEWS=false를 유지하려면 LS 환경변수를 설정하세요.")
            sys.exit(1)
        print("LS증권 뉴스 데이터가 없어 샘플 뉴스 데이터를 사용합니다.")
        news_data = get_sample_news_data()

    result = analyze_news_with_gemini(news_data)
    save_analysis_to_db(result, news_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
