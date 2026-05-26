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
