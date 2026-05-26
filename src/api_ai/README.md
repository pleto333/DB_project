# src/api_ai

LS증권 뉴스 → Gemini AI 분석 → FastAPI 웹서버 파이프라인 모듈

---

## 실행

```bash
# 프로젝트 루트(DB_project/)에서 실행
python3 -m uvicorn src.api_ai.AI:app --host 0.0.0.0 --port 8080
```

---

## 파일 구조

```
src/api_ai/
├── AI.py          진입점. uvicorn용 app 객체 및 CLI main()
├── config.py      환경변수 로드, 상수 정의
├── gemini.py      Gemini API 호출, 프롬프트 빌드, 샘플/더미 데이터
├── ls_api.py      LS증권 API (토큰 발급, 뉴스 수신, 일봉 주가 조회)
├── scheduler.py   10분 자동 분석 스케줄러, KOSPI/KOSDAQ 실시간 지수 WebSocket
└── server.py      FastAPI 앱 및 모든 엔드포인트
```

---

## 환경변수 (.env)

프로젝트 루트의 `.env` 파일에 아래 값을 설정합니다.  
`.env.example`을 복사해서 사용하세요.

| 키 | 설명 | 없을 때 |
|----|------|---------|
| `GEMINI_API_KEY` | Gemini AI API 키 | 서버 종료 |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | MySQL 접속 정보 | DB 저장 실패 |
| `LS_APP_KEY` / `LS_APP_SECRET` | LS증권 OpenAPI 앱 키 | 샘플 뉴스 사용 |
| `LS_ACCESS_TOKEN` | LS증권 접근토큰 (선택) | 자동 발급 |

---

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 서버 상태 확인 |
| POST | `/analyze` | Gemini AI 분석 실행 |
| GET | `/recommendations/latest` | 최신 AI 분석 결과 조회 |
| GET | `/market/indices` | KOSPI/KOSDAQ 실시간 지수 |
| GET | `/stocks/price?codes=005930,000660` | 종목 일봉 주가 (최근 10거래일) |
| GET | `/portfolio?user_id={id}` | 사용자 포트폴리오 조회 |
| POST | `/portfolio` | 포트폴리오 종목 추가 |
| DELETE | `/portfolio` | 포트폴리오 종목 제거 |
| POST | `/register` | 회원가입 |
| POST | `/login` | 로그인 |

---

## 주요 동작

### 자동 스케줄러
서버 시작 시 즉시 1회 실행 후 **10분마다** 반복합니다.
```
LS증권 뉴스 수신 → Gemini 분석 → DB 저장
```
LS 키가 없으면 샘플 뉴스 데이터로 대체합니다.

### 실시간 지수
LS증권 `IJ_` WebSocket TR로 KOSPI(001), KOSDAQ(101) 지수를 실시간 수신합니다.  
장 마감 시간에는 마지막 수신값을 유지하며, LS 키가 없으면 `-`로 표시됩니다.

### 종목 주가 (스파크라인)
LS증권 `t8413` TR (일봉)으로 최근 10거래일 종가를 조회합니다.
- 종목당 **5분 캐시** 적용
- LS API 호출 제한으로 인해 종목 사이 **1.2초 딜레이** 적용
- 장 중에는 전일 종가까지만 반영 (실시간 현재가 아님)

### Gemini 응답 형식
```json
{
  "analysis_date": "2026-05-27",
  "top_themes": ["AI 반도체", "전력 인프라", "조선"],
  "recommendations": [
    {
      "rank": 1,
      "stock_name": "삼성전자",
      "stock_code": "005930",
      "market": "KOSPI",
      "theme": "AI 반도체",
      "reason": "...",
      "news_evidence": "...",
      "expected_momentum": "...",
      "risk": "...",
      "confidence": "상/중/하"
    }
  ],
  "market_news": {
    "kospi": ["뉴스1", "뉴스2", "뉴스3"],
    "kosdaq": ["뉴스1", "뉴스2", "뉴스3"]
  },
  "overall_market_summary": "...",
  "disclaimer": "..."
}
```
