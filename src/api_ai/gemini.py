from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Any

from .config import get_gemini_model, get_gemini_models, is_missing_env_value


def get_sample_news_data() -> str:
    return """
[샘플 뉴스 데이터]
1. 날짜: 2026-05-27
   제목: SK하이닉스·삼성전자, HBM4 수주 경쟁 본격화…엔비디아 납품 기대
   내용: SK하이닉스(000660)가 HBM4 양산 일정을 앞당기며 엔비디아 공급 우위를 유지하고 있다.
   삼성전자(005930)도 HBM4E 인증 작업에 속도를 내고 있으며, 한미반도체(042700)의
   TC본더 장비 수주도 함께 늘어나는 추세다.

2. 날짜: 2026-05-27
   제목: HD현대일렉트릭·LS ELECTRIC, 북미 변압기 수주 잇따라…전력기기 모멘텀 지속
   내용: HD현대일렉트릭(267260)이 미국 전력망 현대화 프로젝트 수주를 연달아 발표했다.
   LS ELECTRIC(010120)도 북미·유럽 데이터센터향 전력기기 공급 계약을 체결하며
   실적 기대감이 커지고 있다.

3. 날짜: 2026-05-27
   제목: HD한국조선해양·한화오션, LNG선 발주 급증…수주 잔고 사상 최대
   내용: HD한국조선해양(009540)이 카타르 LNG 운반선 추가 발주 계약을 체결했다.
   한화오션(042660)도 친환경 암모니아 추진선 수주에 성공하며 조선업 슈퍼사이클
   기대감이 높아지고 있다.

4. 날짜: 2026-05-27
   제목: 삼성바이오로직스·셀트리온, 글로벌 CMO·바이오시밀러 수요 확대
   내용: 삼성바이오로직스(207940)가 글로벌 빅파마와 대규모 위탁생산 계약을 체결했으며
   셀트리온(068270)도 유럽 바이오시밀러 시장 점유율을 높이고 있다.
""".strip()


def get_dummy_analysis_result() -> dict[str, Any]:
    today = datetime.now().strftime("%Y-%m-%d")
    return {
        "analysis_date": today,
        "top_themes": ["AI 반도체", "전력 인프라", "조선"],
        "recommendations": [
            {
                "rank": 1, "stock_name": "삼성전자", "stock_code": "005930", "market": "KOSPI",
                "theme": "AI 반도체", "reason": "샘플 뉴스 기준 AI 서버 투자 확대와 반도체 수요 증가 기대가 있습니다.",
                "news_evidence": "AI 반도체 수요 확대와 HBM 및 첨단 패키징 관련주 관심 뉴스",
                "expected_momentum": "AI 투자 확대 기대에 따른 단기 관심 증가",
                "risk": "단기 급등 부담, 업황 변동, 고객사 투자 속도 둔화 가능성", "confidence": "중",
            },
            {
                "rank": 2, "stock_name": "SK하이닉스", "stock_code": "000660", "market": "KOSPI",
                "theme": "HBM", "reason": "샘플 뉴스 기준 고대역폭 메모리 수요 확대와 직접적으로 연결됩니다.",
                "news_evidence": "글로벌 빅테크의 AI 서버 투자 확대와 HBM 관심 증가",
                "expected_momentum": "HBM 수요 기대에 따른 수급 관심",
                "risk": "메모리 가격 변동과 대형 고객사 투자 계획 변화", "confidence": "중",
            },
            {
                "rank": 3, "stock_name": "HD현대일렉트릭", "stock_code": "267260", "market": "KOSPI",
                "theme": "전력 인프라", "reason": "샘플 뉴스 기준 데이터센터와 전력망 투자 확대 기대와 관련성이 있습니다.",
                "news_evidence": "전력망 증설 필요성과 변압기·전력기기 수주 모멘텀 부각",
                "expected_momentum": "전력기기 수주 기대감",
                "risk": "수주 지연, 원자재 가격, 환율 변동", "confidence": "중",
            },
            {
                "rank": 4, "stock_name": "LS ELECTRIC", "stock_code": "010120", "market": "KOSPI",
                "theme": "전력기기", "reason": "샘플 뉴스 기준 전력 인프라 투자 확대와 연결되는 종목입니다.",
                "news_evidence": "데이터센터와 재생에너지 설비 증가로 전력망 증설 필요성 확대",
                "expected_momentum": "전력 설비 투자 확대 기대",
                "risk": "수주 경쟁 심화와 실적 반영 시차", "confidence": "중",
            },
            {
                "rank": 5, "stock_name": "HD한국조선해양", "stock_code": "009540", "market": "KOSPI",
                "theme": "조선", "reason": "샘플 뉴스 기준 LNG선과 친환경 선박 발주 기대가 있습니다.",
                "news_evidence": "조선 업황 개선 기대와 LNG선·친환경 선박 발주 주목",
                "expected_momentum": "수주 잔고와 선박 발주 기대",
                "risk": "원자재 가격, 환율, 인도 일정 지연 가능성", "confidence": "중",
            },
        ],
        "market_news": {
            "kospi": [
                "외국인 코스피 순매수 3거래일 연속 지속",
                "반도체·전력기기 업종 강세, 시가총액 상위 종목 견인",
                "코스피 2,600선 지지 속 AI 테마 관심 집중",
            ],
            "kosdaq": [
                "코스닥 바이오·이차전지 반등 시도",
                "중소형 AI 관련주 수급 유입 확대",
                "코스닥 외국인 순매수 전환 기대감",
            ],
        },
        "overall_market_summary": "샘플 뉴스 기준 AI 반도체, 전력 인프라, 조선 업종의 뉴스 모멘텀이 상대적으로 강하게 나타납니다.",
        "disclaimer": "이 결과는 웹/API 연동 테스트용 더미 응답이며 매수·매도 추천이 아닙니다.",
    }


def build_prompt(news_data: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""
당신은 한국 주식 시장 전문 AI 애널리스트입니다.
사용자는 LS증권 API를 활용하여 수집한 최신 뉴스 데이터를 바탕으로 투자 참고용 종목 추천 서비스를 만들고 있습니다.

당신의 역할은 아래 뉴스 데이터를 분석하여,
현재 시장에서 뉴스 모멘텀이 강한 한국 상장 주식 5개를 추천하는 것입니다.

중요한 규칙:
- 반드시 제공된 뉴스 데이터에 근거해서만 분석하세요.
- 종목명과 종목코드는 가능한 한 정확하게 작성하세요.
- 잘 모르는 종목코드는 빈 문자열("")로 두세요.
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
6. 뉴스에서 KOSPI와 KOSDAQ 시장 전반에 관한 주요 헤드라인 3개씩 추출합니다.

[최신 뉴스 데이터]
{news_data}

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "analysis_date": "{today}",
  "top_themes": ["핵심 테마 1", "핵심 테마 2", "핵심 테마 3"],
  "recommendations": [
    {{
      "rank": 1, "stock_name": "종목명", "stock_code": "종목코드 또는 빈 문자열",
      "market": "KOSPI 또는 KOSDAQ 또는 빈 문자열", "theme": "관련 테마",
      "reason": "뉴스 기반 추천 이유", "news_evidence": "추천 근거가 된 뉴스 내용 요약",
      "expected_momentum": "예상되는 단기 모멘텀", "risk": "주의해야 할 위험 요소", "confidence": "상/중/하"
    }},
    {{"rank": 2, "stock_name": "종목명", "stock_code": "", "market": "", "theme": "", "reason": "", "news_evidence": "", "expected_momentum": "", "risk": "", "confidence": "중"}},
    {{"rank": 3, "stock_name": "종목명", "stock_code": "", "market": "", "theme": "", "reason": "", "news_evidence": "", "expected_momentum": "", "risk": "", "confidence": "중"}},
    {{"rank": 4, "stock_name": "종목명", "stock_code": "", "market": "", "theme": "", "reason": "", "news_evidence": "", "expected_momentum": "", "risk": "", "confidence": "중"}},
    {{"rank": 5, "stock_name": "종목명", "stock_code": "", "market": "", "theme": "", "reason": "", "news_evidence": "", "expected_momentum": "", "risk": "", "confidence": "중"}}
  ],
  "market_news": {{
    "kospi": ["KOSPI 주요 뉴스 헤드라인 1", "KOSPI 주요 뉴스 헤드라인 2", "KOSPI 주요 뉴스 헤드라인 3"],
    "kosdaq": ["KOSDAQ 주요 뉴스 헤드라인 1", "KOSDAQ 주요 뉴스 헤드라인 2", "KOSDAQ 주요 뉴스 헤드라인 3"]
  }},
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
        return cleaned[start: end + 1]
    return cleaned


def analyze_news_with_gemini(news_data: str) -> dict:
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if is_missing_env_value(api_key):
        print("Gemini API Key가 없습니다. .env 파일에 GEMINI_API_KEY를 설정해 주세요.")
        sys.exit(1)

    prompt = build_prompt(news_data)
    client = genai.Client(api_key=api_key)
    max_retries = int(os.getenv("GEMINI_MAX_RETRIES", "3"))
    response = None
    last_error: Exception | None = None

    for gemini_model in get_gemini_models():
        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=gemini_model,
                    contents=prompt,
                    config={"response_mime_type": "application/json", "temperature": 0.2},
                )
                break
            except Exception as exc:
                last_error = exc
                error_text = str(exc)
                if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                    print("Gemini API 사용량 한도에 도달했습니다.")
                    sys.exit(1)
                if "503" in error_text or "UNAVAILABLE" in error_text:
                    wait = min(2 ** attempt, 10)
                    print(f"Gemini 혼잡. model={gemini_model}, attempt={attempt}/{max_retries}, {wait}초 후 재시도.")
                    time.sleep(wait)
                    continue
                print(f"Gemini API 호출 중 오류: {exc}")
                sys.exit(1)
        if response is not None:
            break
        print(f"{gemini_model} 모델 재시도 실패. 다음 fallback 모델을 시도합니다.")

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
        print(f"Gemini 응답을 JSON으로 파싱하지 못했습니다: {exc}")
        print(f"\n[Gemini 원본 응답]\n{raw_text}")
        sys.exit(1)
