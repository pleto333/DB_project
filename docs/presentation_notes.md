# 발표자료 구성 메모

## 1. DB 설계 보강

### 변경 전 문제점

초기 DB 설계는 `news_articles`, `llm_analysis`, `stock_recommendations`를 분리해 저장했다.
하지만 `news_articles`와 `llm_analysis` 사이의 연결 정보가 없어서, 추천 결과가 어떤 뉴스들을 바탕으로 생성되었는지 추적하기 어려웠다.

### 해결 방법

`analysis_news_articles` 연결 테이블을 추가했다.
이 테이블은 하나의 LLM 분석 결과가 어떤 뉴스 기사들을 입력으로 사용했는지 저장한다.

### 설계 이유

LLM 분석은 보통 여러 개의 뉴스 기사를 한 번에 입력받는다.
또 같은 뉴스 기사가 다른 시점이나 다른 사용자 요청에서 다시 분석될 수도 있다.
따라서 `news_articles`와 `llm_analysis`는 다대다 관계로 보는 것이 자연스럽다.

### 개선 효과

- 추천 결과의 근거 뉴스 추적 가능
- LLM 원본 응답과 최종 추천 종목 비교 가능
- 발표 시 "뉴스 수집 -> LLM 분석 -> 종목 추천" 흐름을 ERD로 명확히 설명 가능
- 추천 결과가 이상할 때 어떤 뉴스 입력 때문인지 확인 가능

### 발표용 한 문장

추천 종목만 저장하는 것이 아니라, 어떤 뉴스 묶음을 LLM이 분석해서 해당 추천이 나왔는지 추적할 수 있도록 뉴스와 분석 결과 사이에 연결 테이블을 추가했습니다.

## 2. 백엔드 API 구현

### 구현 목적

DB에 저장된 LLM 추천 결과를 프론트엔드가 사용할 수 있는 JSON 형태로 전달하기 위해 FastAPI 기반 백엔드 API를 추가했다.

### 구현 내용

- `GET /api/recommendations/latest`: 최신 LLM 분석 결과에서 나온 추천 종목 목록 조회
- `GET /api/analyses/latest/news`: 최신 LLM 분석에 사용된 뉴스 기사 목록 조회
- `GET /api/analyses/{analysis_id}/recommendations`: 특정 분석 결과의 추천 종목 목록 조회
- `GET /api/analyses/{analysis_id}/news`: 특정 분석에 사용된 뉴스 기사 목록 조회

### 개선 효과

- DB에 저장된 결과를 Vue.js 프론트엔드에서 바로 호출할 수 있다.
- 추천 종목과 근거 뉴스 데이터를 분리된 API로 제공할 수 있다.
- 발표 시 "DB 저장 데이터 -> 백엔드 API -> JSON 응답 -> UI 표시" 흐름을 보여줄 수 있다.

### 발표용 한 문장

DB에 저장된 추천 결과와 근거 뉴스를 프론트엔드에서 사용할 수 있도록 FastAPI 기반 JSON API를 구현했습니다.

## 3. DB 실행 환경 정리

### 진행 내용

MySQL 서버가 `localhost:3307` 포트에서 실행되는 환경을 기준으로 DB 접속 설정을 정리했다.
또한 `mysql` CLI가 PATH에 없는 경우에도 스키마와 샘플 데이터를 넣을 수 있도록 `scripts/setup_database.py` 초기화 스크립트를 추가했다.

### 실행 순서

```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="3307"
$env:DB_USER="root"
$env:DB_PASSWORD="내 MySQL 비밀번호"
$env:DB_NAME="stock_prediction_db"
python scripts/setup_database.py
python -m uvicorn app:app --reload
```

### 발표용 한 문장

로컬 MySQL 환경 차이를 줄이기 위해 Python 기반 DB 초기화 스크립트를 추가했고, 이후 API 서버가 해당 DB를 조회해 JSON 응답을 제공하도록 구성했습니다.

## 4. 실제 DB 연동 확인

### 진행 내용

MySQL Server를 `localhost:3307` 포트에서 실행하고, root 계정으로 프로젝트 DB를 생성했다.
`scripts/setup_database.py`를 실행해 스키마와 샘플 데이터를 적재한 뒤 FastAPI 서버에서 실제 DB 조회 응답을 확인했다.

### 확인 결과

- `python scripts/setup_database.py` 실행 결과: `Database setup completed.`
- `GET /api/recommendations/latest` 응답의 `data_source`: `database`
- `GET /api/analyses/latest/news` 응답의 `data_source`: `database`

### 발표용 한 문장

MySQL에 실제 스키마와 샘플 데이터를 적재한 뒤, FastAPI가 DB에서 추천 종목과 근거 뉴스를 조회해 JSON으로 반환하는 것까지 확인했습니다.

## 5. 발표용 대시보드 화면 구현

### 구현 목적

API 응답을 사람이 확인하기 쉬운 화면으로 보여주기 위해 발표용 대시보드 페이지를 추가했다.

### 구현 내용

- `/dashboard` 경로에서 정적 프론트 화면 제공
- `GET /api/recommendations/latest`를 호출해 추천 종목 표시
- `GET /api/analyses/latest/news`를 호출해 추천 근거 뉴스 표시
- 분석 번호, 추천 종목 수, 근거 뉴스 수, 데이터 출처 표시

### 발표용 한 문장

FastAPI에서 제공하는 JSON API를 프론트 화면에서 호출해 추천 종목과 근거 뉴스를 한 화면에 표시하도록 구현했습니다.

## 6. Vue 임시 프론트엔드 구현

### 구현 목적

프론트엔드 담당자가 붙기 전에도 DB 담당자가 API 응답이 화면에 어떻게 표시되는지 확인할 수 있도록 Vue.js 기반 임시 화면을 별도 프로젝트로 구성했다.

### 구현 내용

- `frontend/` 폴더에 Vue + Vite 프로젝트 생성
- Vue 화면에서 `/api/recommendations/latest`와 `/api/analyses/latest/news` 호출
- Vite 개발 서버에서 `/api` 요청을 FastAPI 서버 `http://127.0.0.1:8000`으로 프록시
- `npm run build`로 프론트 빌드 검증 완료
- 브라우저에서 `http://127.0.0.1:5173` 접속 후 실제 DB 데이터 렌더링 확인

### 발표용 한 문장

프론트엔드 담당자에게 전달하기 전 API 연동을 임시로 확인할 수 있도록 Vue.js 화면을 만들고, FastAPI의 추천 종목/근거 뉴스 API와 연결했습니다.

## 7. 샘플 데이터 한글화

### 진행 내용

발표 화면에서 종목명과 추천 이유가 영어로 표시되어 이해가 덜 직관적이었다.
샘플 DB 데이터, demo fallback 데이터, API 응답 예시 문서를 한국어 기준으로 수정했다.

### 확인 결과

- `Samsung Electronics` -> `삼성전자`
- `SK hynix` -> `SK하이닉스`
- 추천 이유와 뉴스 제목/요약도 한국어 문장으로 변경
- Vue 화면에서 한국어 종목명이 렌더링되는 것 확인

### 발표용 한 문장

발표 화면의 가독성을 높이기 위해 샘플 종목명, 추천 이유, 근거 뉴스 내용을 한국어로 정리했습니다.

## 8. 발표용 샘플 데이터 확장

### 진행 내용

DB 구조와 추천 흐름을 더 잘 보여주기 위해 샘플 데이터를 확장했다.
기존에는 뉴스 2개와 추천 종목 2개만 있어 화면과 Workbench에서 확인할 수 있는 내용이 적었다.

### 확장 결과

- 뉴스 기사: 8개
- 추천 가능 종목: 7개
- LLM 분석 결과: 3개
- 추천 결과: 7개
- 뉴스-분석 연결 데이터: 8개

### 추가한 분석 시나리오

- 반도체: 삼성전자, SK하이닉스 추천
- 2차전지: LG에너지솔루션, 삼성SDI, 포스코퓨처엠 추천
- 플랫폼: NAVER, 카카오 관망

### 발표용 한 문장

뉴스 묶음별로 LLM 분석 결과가 생성되고, 각 분석 결과마다 여러 추천 종목과 근거 뉴스가 연결되는 구조를 보여주기 위해 샘플 데이터를 확장했습니다.

## 9. Vue 화면 기능 보강

### 진행 내용

DB 구조가 화면 기능으로 드러나도록 Vue 임시 프론트엔드에 조회 기능을 추가했다.

### 추가 기능

- 분석 결과 선택: `llm_analysis`에 저장된 반도체, 2차전지, 플랫폼 분석 결과를 선택 조회
- 추천 구분 필터: `stock_recommendations.recommendation` 값 기준으로 전체, BUY, WATCH 필터링
- 추천 근거 뉴스 보기: 추천 종목 클릭 시 `analysis_news_articles`로 연결된 근거 뉴스 영역 강조

### 확인 결과

- `/api/analyses` 분석 목록 API 응답 확인
- Vue 화면에서 분석 선택 목록, BUY/WATCH 필터 표시 확인
- WATCH 필터 클릭 시 WATCH 종목만 표시 확인
- 포스코퓨처엠 클릭 시 오른쪽 패널이 `포스코퓨처엠 근거 뉴스`로 변경되는 것 확인

### 발표용 한 문장

분석 결과 선택, 추천 구분 필터, 추천 종목별 근거 뉴스 강조 기능을 추가해 DB 테이블 간 관계가 화면에서도 드러나도록 개선했습니다.
