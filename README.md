# DB_project

뉴스 데이터를 LLM API로 분석해 추천 종목을 제공하는 데이터베이스 팀프로젝트입니다.

## 핵심 산출물

- `sql/schema.sql`: `stock_prediction_db` 데이터베이스 및 전체 테이블 생성 SQL
- `sql/sample_data.sql`: 발표/테스트용 예시 데이터 INSERT SQL
- `src/db/database.py`: Python `mysql-connector-python` 연동 예제 및 추천 결과 JSON 조회 함수
- `docs/table_dictionary.md`: 각 테이블과 컬럼의 의미를 정리한 데이터 사전

## 실행 순서

```powershell
pip install -r requirements.txt
mysql -u root -p < sql/schema.sql
mysql -u root -p stock_prediction_db < sql/sample_data.sql
```

PowerShell에서 DB 접속 정보를 환경변수로 설정합니다.


```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="3306"
$env:DB_USER="root"
$env:DB_PASSWORD="내 MySQL 비밀번호"
$env:DB_NAME="stock_prediction_db"
```

연결 테스트:

```powershell
python src/db/database.py
```

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
