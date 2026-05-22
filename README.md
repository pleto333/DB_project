# DB_project

뉴스 데이터를 LLM API로 분석해 추천 종목을 제공하는 데이터베이스 팀프로젝트입니다.

## 핵심 산출물

- `sql/schema.sql`: `stock_prediction_db` 데이터베이스 및 전체 테이블 생성 SQL
- `sql/sample_data.sql`: 발표/테스트용 예시 데이터 INSERT SQL
- `src/db/database.py`: Python `mysql-connector-python` 연동 예제 및 추천 결과 JSON 조회 함수
- `docs/table_dictionary.md`: 각 테이블과 컬럼의 의미를 정리한 데이터 사전
- `docs/presentation_notes.md`: 발표자료 구성에 사용할 변경 내용 메모
- `docs/api_response_examples.md`: 프론트엔드 전달용 API 응답 예시
- `frontend/`: Vue.js 임시 프론트엔드 화면

## 실행 순서

```powershell
pip install -r requirements.txt
mysql -u root -p < sql/schema.sql
mysql -u root -p stock_prediction_db < sql/sample_data.sql
```

PowerShell에서 DB 접속 정보를 환경변수로 설정합니다.


```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="3307"
$env:DB_USER="root"
$env:DB_PASSWORD="내 MySQL 비밀번호"
$env:DB_NAME="stock_prediction_db"
```

연결 테스트:

```powershell
python src/db/database.py
```

DB 구조 직접 확인:

```powershell
python scripts/inspect_database.py
```

이 스크립트는 테이블 목록, 컬럼 구조, 외래키 관계, 최신 추천 결과, 추천 근거 뉴스를 출력합니다.

MySQL CLI가 PATH에 없다면 Python 초기화 스크립트로 스키마와 샘플 데이터를 넣을 수 있습니다.

```powershell
python scripts/setup_database.py
```

API 서버 실행:

```powershell
python -m uvicorn app:app --reload
```

주요 API:

- `GET /api/recommendations/latest`: 최신 추천 종목 JSON 조회
- `GET /api/analyses/latest/news`: 최신 분석에 사용된 뉴스 JSON 조회
- `GET /api/analyses/{analysis_id}/recommendations`: 특정 분석의 추천 종목 조회
- `GET /api/analyses/{analysis_id}/news`: 특정 분석에 사용된 뉴스 조회

화면 확인:

- `GET /dashboard`: 추천 종목과 근거 뉴스를 보여주는 발표용 대시보드

Vue 임시 프론트엔드 실행:

```powershell
cd frontend
npm install
npm run dev
```

Vue 화면 주소:

- `http://127.0.0.1:5173`

Vue 개발 서버는 `/api` 요청을 FastAPI 서버 `http://127.0.0.1:8000`으로 프록시합니다.
따라서 FastAPI 서버를 먼저 실행한 뒤 Vue 서버를 실행해야 합니다.

Vue 임시 화면 기능:

- 분석 결과 선택: 반도체, 2차전지, 플랫폼 분석 결과를 바꿔가며 조회
- 추천 구분 필터: 전체, BUY, WATCH 필터링
- 추천 근거 뉴스 보기: 추천 종목 클릭 시 해당 분석에 연결된 근거 뉴스 강조

## 프로젝트 구조
```text
데베 팀플
│
├── .gitignore              # venv, pycache, .env 등 제외
├── README.md               # 프로젝트 개요 및 실행 방법
├── requirements.txt        # 필요 라이브러리 목록
│
├── src/                    # 소스 코드 메인 폴더
│   ├── ui/                 # 김현석 및 신휘서 님 (UI 관련 코드)
│   ├── api_ai/             # 이대현 님 (뉴스 크롤링, 감성 분석)
│   └── db/                 # 유승빈 님 (SQL 스크립트, DB 연결 로직)
│
└── tests/                  # 테스트 코드 폴더
