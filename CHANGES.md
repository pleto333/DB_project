# 백엔드 변경 사항 정리

> 백엔드 담당자가 추가/수정한 내용입니다. 팀원 모두 읽어주세요.

---

## 1. 실행 방법

### 사전 조건

```bash
pip install fastapi uvicorn google-genai websockets requests python-dotenv mysql-connector-python
```

### 서버 실행

```bash
# 프로젝트 루트(DB_project/)에서 실행
python3 -m uvicorn src.api_ai.AI:app --host 0.0.0.0 --port 8080
```

### .env 파일

`DB_project/.env` 파일이 있어야 정상 동작합니다.  
없으면 Gemini 분석은 더미 데이터로, LS증권 뉴스/주가는 샘플 데이터로 동작합니다.

필수 키:
```
DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME   ← MySQL 접속 정보
GEMINI_API_KEY                                         ← Gemini AI 키
LS_APP_KEY / LS_APP_SECRET                            ← LS증권 OpenAPI 키 (없으면 샘플 뉴스 사용)
```

---

## 2. 파일 구조 변경 (코드 분할)

기존 `AI.py` 한 파일(1200줄+)을 6개 모듈로 분리했습니다.

```
src/api_ai/
├── AI.py          ← 진입점만 남김 (uvicorn 실행용 app 객체 포함)
├── config.py      ← 환경변수, 상수, .env 로드
├── gemini.py      ← Gemini API 호출, 프롬프트, 샘플/더미 데이터
├── ls_api.py      ← LS증권 API (토큰 발급, 뉴스, 일봉 주가)
├── scheduler.py   ← 10분 자동 분석, 실시간 지수 WebSocket
└── server.py      ← FastAPI 앱, 모든 엔드포인트 정의
```

---

## 3. API 엔드포인트 목록

Base URL: `http://localhost:8080`

| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 서버 상태 확인 |
| POST | `/analyze` | Gemini AI 분석 실행 |
| GET | `/recommendations/latest` | 최신 AI 분석 결과 조회 |
| GET | `/market/indices` | KOSPI/KOSDAQ 실시간 지수 |
| GET | `/stocks/price?codes=005930,000660` | 종목 일봉 주가 (최근 10거래일) |
| GET | `/portfolio?user_id=1` | 사용자 포트폴리오 조회 |
| POST | `/portfolio` | 포트폴리오 종목 추가 |
| DELETE | `/portfolio` | 포트폴리오 종목 제거 |
| POST | `/register` | 회원가입 |
| POST | `/login` | 로그인 |

---

## 4. DB 변경 사항 (DB 담당자 필독)

### `portfolio` 테이블 추가 필요

현재 로컬 MySQL에는 직접 생성했지만, `sql/schema.sql`에 아직 반영이 안 되어 있습니다.  
**`schema.sql`에 아래 DDL을 추가해주세요.**

```sql
CREATE TABLE IF NOT EXISTS portfolio (
    portfolio_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id      BIGINT UNSIGNED NOT NULL,
    stock_code   VARCHAR(20)     NOT NULL,
    stock_name   VARCHAR(100)    NOT NULL,
    added_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_stock (user_id, stock_code),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
```

### `database.py`에 추가된 함수

```python
add_portfolio_item(user_id, stock_code, stock_name)   # 포트폴리오 추가 (중복 무시)
remove_portfolio_item(user_id, stock_code)             # 포트폴리오 제거
get_portfolio_by_user(user_id)                         # 사용자 포트폴리오 조회
add_user(username, email, password_hash)               # 회원가입
get_user_by_username(username)                         # 로그인용 유저 조회
get_latest_analysis_json()                             # 최신 AI 분석 결과 조회
```

---

## 5. 주요 기능 설명

### 자동 스케줄러
서버 시작 시 즉시 실행, 이후 **10분마다** LS증권 뉴스 → Gemini 분석 → DB 저장을 자동으로 반복합니다.

### 실시간 지수 (KOSPI / KOSDAQ)
LS증권 `IJ_` WebSocket TR을 통해 실시간으로 수신합니다.  
LS 키가 없거나 장 마감 시간에는 `-/-`로 표시됩니다.

### 종목 추천 그래프
LS증권 `t8413` TR (일봉)으로 최근 10거래일 종가를 가져옵니다.  
- 주가/등락률: 전일 종가 대비 당일 종가 기준  
- **장 중에는 전일 종가까지만 반영** (실시간 현재가 아님)  
- 종목당 **5분 캐시** 적용  
- LS API 호출 제한(연속 요청 제한)으로 종목 사이 1.2초 딜레이 있음

### 회원 인증
- 비밀번호: SHA-256 해시 저장
- 세션: Vue `localStorage`에 `user_id`, `username` 저장 (JWT 미사용)

---

## 6. 프론트엔드 담당자 참고

- API Base URL: `http://localhost:8080` (`MainView.vue`의 `BASE_URL` 상수)
- 로그인 응답: `{ user_id, username, email }` → `localStorage`에 저장
- `/portfolio` DELETE 요청은 body에 JSON을 담아야 합니다 (`axios.delete(url, { data: {...} })`)
- CORS 허용 origin: `localhost:3000`, `localhost:5173` (필요 시 `.env`의 `CORS_ALLOW_ORIGINS` 추가)

---

## 7. DB 연동 전면 개선 (2026-05-27)

> **배경**: 과제 요건상 모든 테이블이 쓰기(INSERT) + 읽기(SELECT) + 화면 표시까지 이루어져야 함.  
> 기존 코드는 DB에 데이터가 저장되고 있었으나 일부 테이블은 조회 없이 JSON blob이나 하드코딩 데이터를 사용.

---

### 7-1. `stocks` + `stock_recommendations` 읽기 연결

**문제**  
`llm_analysis.response_json` JSON blob을 그대로 파싱해 추천 목록을 반환.  
`stocks`, `stock_recommendations` 테이블에 데이터가 쌓여도 읽지 않는 상태였음.

**변경 파일**: `src/db/database.py` — `get_latest_analysis_json()`

```python
# 이전: response_json blob 그대로 반환
return json.loads(meta["response_json"])

# 이후: stock_recommendations JOIN stocks 쿼리
SELECT sr.rank_no, sr.recommendation, sr.reason, sr.confidence,
       s.stock_code, s.stock_name, s.market
FROM stock_recommendations sr
JOIN stocks s ON s.stock_id = sr.stock_id
WHERE sr.analysis_id = %s
```

`response_json`은 `theme`, `news_evidence`, `expected_momentum`, `risk` 보조 필드 보완용으로만 사용.

---

### 7-2. `news_articles` 쓰기 + 읽기 연결

**문제**  
스케줄러가 LS API 뉴스를 Gemini에 넘기고 분석 결과만 저장. 뉴스 원문은 버려짐.  
뉴스 탭은 AI 분석 결과의 `news_evidence` 텍스트를 표시.

**변경 파일**
- `src/api_ai/scheduler.py` — `_save_news_to_db()` 추가
- `src/db/database.py` — `get_latest_news_articles()`, `get_news_by_stock()` 추가
- `src/api_ai/server.py` — `GET /news/latest`, `GET /stocks/{code}/news` 추가
- `src/ui/src/views/MainView.vue` — `loadNewsArticles()` 추가
- `src/ui/src/views/StockDetailView.vue` — 관련 뉴스 DB 연결

**쓰기** (`scheduler.py`)
```python
def _save_news_to_db(news_data, proj_root):
    # "N. 날짜: ...\n   제목: ...\n   내용: ..." 형식 파싱
    blocks = re.split(r'\n\d+\.\s+날짜:', news_data)
    for block in blocks[1:]:
        save_news_article(title=..., url=..., summary=...)
# save_analysis_to_db() 성공 직후 자동 호출
```

**읽기 1 — 뉴스 탭**
```
news_articles → GET /news/latest → MainView 뉴스 탭
```

**읽기 2 — 종목 상세 관련 뉴스**
```sql
-- GET /stocks/{code}/news?name=종목명
SELECT * FROM news_articles
WHERE title LIKE '%종목명%' OR summary LIKE '%종목명%'
ORDER BY collected_at DESC LIMIT 5
```

---

### 7-3. `stocks.market` 화면 표시 연결

**문제**: `StockDetailView.vue` 템플릿에 `· 코스피` 하드코딩.

**변경 파일**: `src/ui/src/views/StockDetailView.vue`

```html
<!-- 이전 -->
<p class="hero-code">{{ stock.code }} · 코스피</p>

<!-- 이후 -->
<p class="hero-code">{{ stock.code }} · {{ stock.market }}</p>
```

`stock.market`은 JOIN 쿼리의 `s.market` 값(KOSPI/KOSDAQ 등)을 사용.

---

### 7-4. `stock_recommendations.recommendation` 화면 표시 연결

**문제**: DB에 BUY/WATCH로 저장되어 있으나, 상세 페이지에서 `confidence !== '하'`로 재판단해 DB 값 무시.

**변경 파일**: `src/ui/src/views/StockDetailView.vue`

```javascript
// 이전
recommend: rec.confidence !== '하'

// 이후
recommend: rec.recommendation === 'BUY'  // DB 값 직접 사용
```

---

### 7-5. `portfolio.added_at` 화면 표시 연결

**문제**: API가 `added_at`을 반환하지만 `loadPortfolio()` 매핑에서 누락.

**변경 파일**: `src/ui/src/views/MainView.vue`

```javascript
// 이전
portfolio.value = items.map(item => ({ name, code, price, change }))

// 이후
portfolio.value = items.map(item => ({
  name, code, price, change,
  addedAt: item.added_at || ''   // 포트폴리오 카드에 "추가 N분 전" 표시
}))
```

---

### 7-6. 종목 검색 DB 연결

**문제**: 포트폴리오 탭 검색이 7개짜리 하드코딩 배열을 필터링.

**변경 파일**
- `src/db/database.py` — `search_stocks()` 추가
- `src/api_ai/server.py` — `GET /stocks/search` 추가
- `src/ui/src/views/MainView.vue` — `searchStocks()` 실제 API 호출로 교체

```sql
-- database.py search_stocks()
SELECT stock_code, stock_name, market FROM stocks
WHERE (stock_code LIKE %s OR stock_name LIKE %s)
  AND stock_code NOT LIKE 'TBD\_%'
ORDER BY ... LIMIT 10
```

---

### 7-7. 추가 신규 엔드포인트 목록

| Method | Path | 설명 |
|--------|------|------|
| GET | `/news/latest` | 최근 수집 뉴스 20건 (`news_articles`) |
| GET | `/stocks/{code}/news?name=` | 종목 관련 뉴스 (`news_articles` 검색) |
| GET | `/stocks/search?query=` | 종목명·코드 검색 (`stocks` 테이블) |
| GET | `/stocks/realtime?code=` | 실시간 현재가 (t1102 / t8413 fallback) |

---

### 7-8. 기타 버그 수정

| 항목 | 내용 |
|------|------|
| `sample_data.sql` 영어 더미 뉴스 | DB에 박혀있던 "Example News" 2건 삭제 |
| 가격 0원 표시 | t8413 비거래일 `close: 0` 필터링 (`if val > 0`) |
| 60초마다 가격 초기화 | `loadRecommendations()` 재호출 시 기존 price/sparkline 보존 |
| 스케줄러 재시도 로직 | `sys.exit(1)` → 커스텀 예외, 실패 시 1~3분 후 재시도 |
| 포트폴리오 500 오류 | `user_id: 'hong123'` 하드코딩 → `localStorage.get('user_id')` |

---

### 최종 테이블 사용 현황

| 테이블 | 쓰기 | 읽기 | 화면 |
|--------|------|------|------|
| `users` | 회원가입 | 로그인 인증 | ✅ |
| `stocks` | 스케줄러 | 추천 목록 JOIN | ✅ |
| `llm_analysis` | 스케줄러 | 추천 목록 조회 | ✅ |
| `stock_recommendations` | 스케줄러 | 추천 목록 JOIN | ✅ |
| `news_articles` | 스케줄러 | 뉴스 탭 / 종목 상세 관련 뉴스 | ✅ |
| `portfolio` | 북마크 추가·제거 | 포트폴리오 탭 (추가일 포함) | ✅ |
