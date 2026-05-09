# 테이블별 컬럼 설명

서비스 목적: LS증권 API에서 가져온 뉴스 데이터를 LLM API로 분석하고, 추천 종목을 JSON 형태로 UI에 전달한다.

## 1. users

로그인 사용자 정보.

| 컬럼명 | 설명 |
| --- | --- |
| user_id | 사용자 고유 번호 |
| username | 로그인 아이디 |
| email | 이메일 |
| password_hash | 암호화된 비밀번호 |
| created_at | 생성 시간 |
| updated_at | 수정 시간 |

## 2. stocks

추천 가능한 종목 정보.

| 컬럼명 | 설명 |
| --- | --- |
| stock_id | 종목 고유 번호 |
| stock_code | 종목 코드 |
| stock_name | 종목명 |
| market | 주식 시장 |
| created_at | 생성 시간 |
| updated_at | 수정 시간 |

## 3. news_articles

LS증권 API에서 가져온 뉴스 정보.

| 컬럼명 | 설명 |
| --- | --- |
| article_id | 뉴스 고유 번호 |
| title | 뉴스 제목 |
| summary | 뉴스 요약 |
| url | 뉴스 링크 |
| url_hash | URL 중복 방지값 |
| publisher | 언론사 |
| source | 뉴스 출처 |
| published_at | 뉴스 발행 시간 |
| collected_at | 뉴스 수집 시간 |
| created_at | 생성 시간 |
| updated_at | 수정 시간 |

## 4. llm_analysis

LLM API 분석 결과.

| 컬럼명 | 설명 |
| --- | --- |
| analysis_id | LLM 분석 고유 번호 |
| user_id | 요청 사용자 번호 |
| model_name | 사용한 LLM 모델명 |
| input_summary | LLM에 전달한 뉴스 요약 |
| response_json | LLM 원본 응답 JSON |
| analyzed_at | 분석 시간 |
| created_at | 생성 시간 |
| updated_at | 수정 시간 |

## 5. stock_recommendations

LLM 분석으로 나온 추천 종목.

| 컬럼명 | 설명 |
| --- | --- |
| recommendation_id | 추천 결과 고유 번호 |
| analysis_id | 어떤 LLM 분석 결과인지 |
| stock_id | 추천 종목 번호 |
| rank_no | 추천 순위 |
| recommendation | 추천 상태, BUY 또는 WATCH |
| reason | 추천 이유 |
| confidence | 추천 신뢰도 |
| created_at | 생성 시간 |
| updated_at | 수정 시간 |

## UI 전달 JSON 예시

```json
{
  "recommendations": [
    {
      "rank_no": 1,
      "stock_code": "005930",
      "stock_name": "Samsung Electronics",
      "recommendation": "BUY",
      "reason": "AI semiconductor demand is positive.",
      "confidence": 0.87
    }
  ]
}
```
