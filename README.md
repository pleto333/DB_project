# 증권사 뉴스 기반 주식 종목 추천 서비스

데이터베이스 과목 프로젝트입니다. LS증권 API 등으로 수집한 뉴스 데이터를 LLM API로 분석하고, 관련 주식 종목 추천 결과를 JSON 형태로 프론트엔드에 보여주는 서비스를 목표로 합니다.

현재 구현은 DB 설계와 샘플 데이터, FastAPI 조회 API, Vue 임시 화면까지 확인할 수 있는 상태입니다. 실제 LS증권 API 연동과 LLM 분석 호출은 팀 내 API/AI 담당자가 이어서 구현할 예정입니다.

## 현재 구현된 내용

- MySQL 스키마 설계
- 샘플 뉴스, 분석 결과, 추천 종목 데이터
- 뉴스 원본과 LLM 분석 결과를 연결하는 `analysis_news_articles` 테이블
- FastAPI 기반 조회 API
- Vue + Vite 기반 임시 프론트엔드 화면
- 발표용 PPT와 미리보기 이미지
- DB 초기화/점검용 Python 스크립트

## 주요 산출물

- `sql/schema.sql`: 데이터베이스와 테이블 생성 SQL
- `sql/sample_data.sql`: 발표 및 테스트용 샘플 데이터
- `src/db/database.py`: MySQL 연결 및 조회 함수
- `src/db/demo_data.py`: DB 연결 실패 시 사용하는 임시 데모 데이터
- `app.py`: FastAPI 서버
- `frontend/`: Vue 임시 프론트엔드
- `scripts/setup_database.py`: MySQL CLI 없이 DB 초기화
- `scripts/inspect_database.py`: 테이블 구조와 주요 조회 결과 확인
- `docs/table_dictionary.md`: 테이블별 컬럼 설명
- `docs/database_design.md`: DB 설계 설명
- `docs/api_integration_guide.md`: 실제 뉴스 API 연동 가이드
- `docs/frontend_handoff.md`: 프론트엔드 수정 및 교체 가이드
- `docs/github_pages_deploy.md`: GitHub Pages 공유용 배포 가이드
- `docs/local_tunnel_share.md`: 로컬 API까지 연결된 화면을 임시 공유하는 방법
- `output/stock_news_recommendation_presentation.pptx`: 발표용 PPT

## 실행 방법

### 1. Python 패키지 설치

```powershell
pip install -r requirements.txt
```

### 2. MySQL 환경 변수 설정

현재 로컬 MySQL은 `localhost:3307` 기준으로 맞춰두었습니다.

```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="3307"
$env:DB_USER="root"
$env:DB_PASSWORD="1234"
$env:DB_NAME="stock_prediction_db"
```

### 3. DB 초기화

MySQL CLI가 없어도 Python 스크립트로 스키마와 샘플 데이터를 넣을 수 있습니다.

```powershell
python scripts/setup_database.py
```

DB 구조를 직접 확인하려면 다음 명령을 사용합니다.

```powershell
python scripts/inspect_database.py
```

### 4. FastAPI 서버 실행

```powershell
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

주요 API:

- `GET /api/analyses`: 분석 결과 목록 조회
- `GET /api/recommendations`: 전체 추천 종목 조회
- `GET /api/analyses/news`: 전체 근거 뉴스 조회
- `GET /api/recommendations/latest`: 최신 분석 기준 추천 종목 조회
- `GET /api/analyses/latest/news`: 최신 분석 기준 근거 뉴스 조회
- `GET /api/analyses/{analysis_id}/recommendations`: 특정 분석의 추천 종목 조회
- `GET /api/analyses/{analysis_id}/news`: 특정 분석의 근거 뉴스 조회

### 5. Vue 임시 프론트엔드 실행

```powershell
cd frontend
npm install
npm run dev
```

브라우저에서 접속:

```text
http://127.0.0.1:5173
```

Vue 개발 서버는 `/api` 요청을 FastAPI 서버 `http://127.0.0.1:8000`으로 프록시합니다. 따라서 FastAPI 서버를 먼저 실행한 뒤 Vue 서버를 실행해야 실제 DB 데이터를 볼 수 있습니다.

## 팀원 TODO

### API 담당 TODO

- [ ] LS증권 API 사용 신청 및 인증키 발급
- [ ] `docs/api_integration_guide.md`를 참고해 실제 뉴스 수집 흐름 구현
- [ ] 뉴스 조회 API 엔드포인트와 요청/응답 형식 확인
- [ ] 뉴스 수집 스크립트 또는 백엔드 서비스 구현
- [ ] 수집한 뉴스 데이터를 `news_articles` 테이블에 저장
- [ ] 중복 뉴스 방지를 위해 `url_hash` 생성 로직 확정
- [ ] 실제 API 장애 시 재시도/로그 처리 방식 정리
- [ ] 실제 뉴스 수집 시각과 발행 시각을 구분해서 저장

### LLM/AI 담당 TODO

- [ ] 사용할 LLM API와 모델 결정
- [ ] 뉴스 묶음을 LLM에 전달할 프롬프트 설계
- [ ] LLM 응답 JSON 형식 확정
- [ ] 분석 결과를 `llm_analysis.response_json`에 저장
- [ ] 추천 종목, 추천 이유, 신뢰도를 `stock_recommendations`에 저장
- [ ] 분석에 사용된 뉴스 목록을 `analysis_news_articles`에 연결
- [ ] LLM 응답 오류 또는 JSON 파싱 실패 처리

### 프론트엔드 담당 TODO

- [ ] 현재 Vue 화면을 유지할지 새 디자인으로 교체할지 결정
- [ ] 실제 API 응답 형식에 맞춰 화면 데이터 매핑 수정
- [ ] 추천 종목 상세 보기 또는 모달 추가 여부 결정
- [ ] 뉴스 원문 링크, 신뢰도, 추천 사유 표시 방식 정리
- [ ] 모바일 화면 반응형 디자인 점검
- [ ] 임시 시장 데이터 영역을 실제 API 또는 제거 대상으로 정리

### DB 담당 TODO

- [ ] 실제 LS증권 API 응답에 맞춰 `news_articles` 컬럼 보강 여부 검토
- [ ] 실제 LLM JSON 구조에 맞춰 `llm_analysis.response_json` 예시 갱신
- [ ] 추천 결과 이력 관리 정책 확정
- [ ] 사용자별 추천 요청을 저장할지 여부 결정
- [ ] 최종 ERD와 테이블 명세 발표자료 반영

## 현재 한계

- LS증권 API와 LLM API는 아직 실제 연결 전입니다.
- Vue 화면은 발표와 데이터 흐름 확인을 위한 임시 화면입니다.
- 환율, 코스피, 공포지수, 업종별 등락률은 현재 정적 샘플 데이터입니다.
- GitHub Pages 같은 정적 호스팅에서는 FastAPI/MySQL이 함께 실행되지 않습니다.
- GitHub Pages 배포본에서는 API 실패 시 프론트 내부의 `static-demo` 데이터가 표시됩니다.

## 참고 문서

- [프론트엔드 수정 및 교체 가이드](docs/frontend_handoff.md)
- [실제 뉴스 API 연동 가이드](docs/api_integration_guide.md)
- [GitHub Pages 배포 가이드](docs/github_pages_deploy.md)
- [로컬 터널 공유 가이드](docs/local_tunnel_share.md)
- [DB 설계 설명](docs/database_design.md)
- [테이블 컬럼 설명](docs/table_dictionary.md)
- [발표 구성 메모](docs/ppt_slide_plan.md)
