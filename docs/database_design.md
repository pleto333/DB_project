# DB 설계 요약

## 서비스 변경 방향

기존 보유 주식 수익률/가격예측 기능은 제외한다.
새 서비스는 LS증권 API에서 가져온 뉴스 데이터를 LLM API로 분석하고, 추천 종목만 UI에 전달한다.

## 핵심 흐름

1. 사용자가 로그인한다.
2. LS증권 API에서 뉴스 데이터를 가져온다.
3. 뉴스 제목/요약을 LLM API에 전달한다.
4. LLM이 추천 종목과 추천 이유를 반환한다.
5. 추천 결과를 DB에 저장한다.
6. UI에는 추천 종목 JSON을 전달한다.

## 테이블

| 테이블 | 역할 |
| --- | --- |
| users | 로그인 사용자 저장 |
| stocks | 추천 가능한 종목 저장 |
| news_articles | 수집한 뉴스 저장 |
| llm_analysis | LLM 원본 분석 결과 저장 |
| stock_recommendations | 추천 종목 결과 저장 |

## 관계

```text
users (1) ── (N) llm_analysis
llm_analysis (1) ── (N) stock_recommendations
stocks (1) ── (N) stock_recommendations
```

## UI 전달 JSON

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
