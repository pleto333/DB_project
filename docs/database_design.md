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
| analysis_news_articles | LLM 분석에 사용된 뉴스 연결 |
| stock_recommendations | 추천 종목 결과 저장 |

## DB 설계 보강 내용

처음 설계에서는 `news_articles`와 `llm_analysis`가 직접 연결되어 있지 않았다.
이 경우 추천 결과가 저장되더라도 어떤 뉴스들이 LLM 입력으로 사용되었는지 추적하기 어렵다.

이를 보완하기 위해 `analysis_news_articles` 연결 테이블을 추가했다.
하나의 LLM 분석은 여러 개의 뉴스를 입력으로 사용할 수 있고, 하나의 뉴스도 여러 분석에서 재사용될 수 있으므로 다대다 관계로 설계했다.

이 보강으로 추천 결과 검증 흐름이 명확해졌다.

```text
뉴스 원본 확인 -> LLM 분석 결과 확인 -> 추천 종목과 추천 이유 확인
```

## 관계

```text
users (1) ── (N) llm_analysis
news_articles (N) ── (N) llm_analysis
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
      "stock_name": "삼성전자",
      "recommendation": "BUY",
      "reason": "AI 서버 투자 확대로 메모리와 반도체 수요 증가가 기대된다.",
      "confidence": 0.87
    }
  ]
}
```
