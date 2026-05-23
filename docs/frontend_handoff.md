# 프론트엔드 수정 및 교체 가이드

현재 `frontend/` 폴더는 최종 프론트엔드라기보다 DB/API 흐름을 눈으로 확인하기 위한 임시 Vue 화면입니다. 프론트엔드 담당자가 새 화면으로 교체하거나 디자인을 수정할 때 참고할 수 있도록 구조와 수정 포인트를 정리합니다.

## 현재 프론트엔드 구조

```text
frontend/
  index.html
  package.json
  vite.config.js
  src/
    main.js
    App.vue
    style.css
```

- `src/App.vue`: 화면 구조, API 호출, 상태 관리가 들어있는 메인 컴포넌트
- `src/style.css`: 전체 디자인과 반응형 스타일
- `vite.config.js`: 개발 서버 설정과 `/api` 프록시 설정

## 실행 방법

백엔드 서버를 먼저 실행합니다.

```powershell
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

그 다음 프론트엔드 개발 서버를 실행합니다.

```powershell
cd frontend
npm install
npm run dev
```

접속 주소:

```text
http://127.0.0.1:5173
```

## 현재 화면에서 하는 일

현재 Vue 화면은 다음 기능을 임시로 구현해두었습니다.

- 분석 결과 선택: 전체, 반도체, 2차전지, 플랫폼 등
- 추천 구분 필터: 전체, BUY, WATCH
- 추천 종목 목록 표시
- 추천 이유와 신뢰도 표시
- 분석에 사용된 뉴스 목록 표시
- 추천 종목 클릭 시 근거 뉴스 영역 강조
- 발표용 시장 정보 영역 표시
  - 환율
  - 공포지수
  - 코스피 차트
  - 업종별 등락률 TOP5

## 사용하는 API

현재 화면은 아래 API를 호출합니다.

| 화면 기능 | API |
| --- | --- |
| 분석 결과 목록 | `GET /api/analyses` |
| 전체 추천 종목 | `GET /api/recommendations` |
| 전체 근거 뉴스 | `GET /api/analyses/news` |
| 특정 분석 추천 종목 | `GET /api/analyses/{analysis_id}/recommendations` |
| 특정 분석 근거 뉴스 | `GET /api/analyses/{analysis_id}/news` |

개발 중에는 `vite.config.js`에서 `/api` 요청을 FastAPI 서버로 프록시합니다.

```js
server: {
  proxy: {
    "/api": "http://127.0.0.1:8000",
  },
}
```

## 실제 프론트로 교체할 때 수정할 부분

### 1. 디자인만 바꾸는 경우

디자인만 바꾸려면 주로 아래 파일을 수정하면 됩니다.

```text
frontend/src/style.css
```

추천 수정 포인트:

- `:root`의 색상 변수 변경
- `.hero` 영역 디자인 변경
- `.recommendation-card` 추천 카드 디자인 변경
- `.news-card` 뉴스 카드 디자인 변경
- `.metrics` 요약 카드 디자인 변경
- `.sector-dashboard` 시장 정보 영역 수정 또는 제거

### 2. 화면 구조를 바꾸는 경우

화면 배치나 컴포넌트 구조를 바꾸려면 아래 파일을 수정합니다.

```text
frontend/src/App.vue
```

주요 영역:

- `<script setup>`: 상태, API 호출, 필터 로직
- `<template>`: 실제 화면 HTML 구조
- `loadDashboard()`: 처음 화면을 불러올 때 실행되는 함수
- `loadAnalysisData()`: 선택한 분석 결과에 맞춰 추천/뉴스 데이터를 불러오는 함수
- `filteredRecommendations`: BUY/WATCH 필터링 결과

### 3. API 응답 형식이 바뀌는 경우

백엔드 API 응답 구조가 바뀌면 `App.vue`의 데이터 매핑 부분을 수정해야 합니다.

현재 추천 종목은 대략 아래 형식을 기대합니다.

```json
{
  "recommendations": [
    {
      "analysis_id": 1,
      "rank_no": 1,
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "recommendation": "BUY",
      "reason": "추천 이유",
      "confidence": 0.87,
      "theme": "반도체"
    }
  ]
}
```

현재 뉴스 데이터는 대략 아래 형식을 기대합니다.

```json
{
  "news_articles": [
    {
      "analysis_id": 1,
      "article_id": 1,
      "title": "뉴스 제목",
      "summary": "뉴스 요약",
      "publisher": "언론사",
      "published_at": "2026-05-10 10:40:00",
      "url": "https://example.com",
      "theme": "반도체"
    }
  ]
}
```

응답 필드명이 바뀌면 `recommendations.value = ...`, `newsArticles.value = ...` 부분과 템플릿의 `item.stock_name`, `article.title` 같은 참조를 함께 바꿔야 합니다.

## 임시 시장 정보 영역

현재 환율, 공포지수, 코스피 차트, 업종별 등락률은 실제 API가 아니라 `App.vue` 상단의 정적 데이터입니다.

관련 상수:

```js
marketTickerItems
exchangeRate
fearIndex
kospiChart
sectorDashboard
```

프론트 담당자가 선택할 수 있는 방향:

- 발표용이면 그대로 유지
- 실제 서비스처럼 보이게 하려면 별도 시장 데이터 API 연결
- 주식 추천 서비스 핵심만 남기려면 시장 정보 영역 제거

## 컴포넌트 분리 추천

현재는 임시 화면이라 `App.vue` 하나에 대부분의 코드가 들어있습니다. 최종 프론트로 발전시키려면 아래처럼 컴포넌트를 나누는 것이 좋습니다.

```text
src/components/
  AnalysisSelector.vue
  RecommendationList.vue
  RecommendationCard.vue
  SourceNewsList.vue
  MarketSidebar.vue
  SectorDashboard.vue
```

분리 기준:

- API 호출과 상태 관리는 `App.vue` 또는 별도 store에서 관리
- 카드/리스트/대시보드는 재사용 가능한 컴포넌트로 분리
- CSS는 컴포넌트별 scoped style 또는 공통 CSS 변수로 관리

## 배포할 때 주의할 점

정적 호스팅만 사용하는 경우, 예를 들어 GitHub Pages나 Vercel의 정적 배포만 사용하면 FastAPI와 MySQL은 같이 실행되지 않습니다.

실제 서비스처럼 배포하려면 아래 구성이 필요합니다.

```text
Vue 프론트엔드 배포
FastAPI 백엔드 배포
MySQL 데이터베이스 배포
환경 변수 설정
CORS 설정
```

발표용 공유 링크만 필요하면 샘플 데이터를 프론트에 포함한 정적 데모 화면을 따로 만드는 방식도 가능합니다.

## 프론트 담당자에게 전달할 핵심

- 현재 화면은 완성본이 아니라 DB/API 흐름 확인용 임시 화면입니다.
- `frontend/src/App.vue`에서 API 호출과 화면 구조를 확인할 수 있습니다.
- `frontend/src/style.css`에서 디자인을 거의 전부 수정할 수 있습니다.
- API 담당자가 실제 응답 형식을 확정하면 필드명에 맞춰 데이터 매핑을 수정해야 합니다.
- 시장 정보 영역은 현재 샘플 데이터이므로 실제 API 연결 또는 제거 여부를 결정해야 합니다.
