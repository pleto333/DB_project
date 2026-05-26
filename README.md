# DB_project

LS증권 뉴스 데이터를 Gemini AI로 분석해 추천 종목을 제공하는 데이터베이스 팀프로젝트입니다.

## 핵심 산출물

- `sql/schema.sql`: `stock_prediction_db` 데이터베이스 및 전체 테이블 생성 SQL
- `sql/sample_data.sql`: 발표/테스트용 예시 데이터 INSERT SQL
- `src/db/database.py`: Python `mysql-connector-python` 연동 및 추천 결과 JSON 조회 함수
- `src/api_ai/`: LS증권 뉴스 수신 → Gemini AI 분석 → FastAPI 웹서버 ([상세 문서](src/api_ai/README.md))
- `docs/table_dictionary.md`: 각 테이블과 컬럼의 의미를 정리한 데이터 사전

## 실행 순서

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. DB 초기화

```bash
mysql -u root -p < sql/schema.sql
mysql -u root -p stock_prediction_db < sql/sample_data.sql
```

### 3. 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다. `.env.example`을 복사해서 값을 채우세요.

```bash
cp .env.example .env
# .env 파일을 열어 DB_HOST, DB_PASSWORD, GEMINI_API_KEY 등 입력
```

### 4. 백엔드 서버 실행

```bash
python3 -m uvicorn src.api_ai.AI:app --host 0.0.0.0 --port 8080
```

### 5. 프론트엔드 실행

```bash
cd src/ui
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

---

## 프로젝트 구조

```text
DB_project
│
├── .env.example            # 환경변수 템플릿 (복사 후 .env로 사용)
├── .gitignore              # venv, pycache, .env 등 제외
├── README.md               # 프로젝트 개요 및 실행 방법
├── requirements.txt        # 필요 라이브러리 목록
│
├── sql/                    # 유승빈 님 (DB 스키마 및 샘플 데이터)
│   ├── schema.sql
│   └── sample_data.sql
│
├── src/
│   ├── ui/                 # 김현석 · 신휘서 님 (Vue.js 프론트엔드)
│   ├── api_ai/             # 이대현 님 (LS증권 뉴스 · Gemini AI · FastAPI 서버)
│   └── db/                 # 유승빈 님 (SQL 스크립트, DB 연결 로직)
│
└── tests/                  # 테스트 코드
```
