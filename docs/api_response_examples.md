# API 응답 예시

현재 로컬 MySQL 서버를 `localhost:3307`에서 실행하고 샘플 데이터를 적재한 뒤 API 응답을 확인했다.
`data_source` 값이 `database`이면 실제 MySQL DB에서 조회한 결과라는 뜻이다.

## 최신 추천 종목 조회

요청:

```http
GET /api/recommendations/latest
```

응답 예시:

```json
{
  "analysis_id": 1,
  "recommendations": [
    {
      "rank_no": 1,
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "recommendation": "BUY",
      "reason": "AI 서버 투자 확대로 메모리와 반도체 수요 증가가 기대된다.",
      "confidence": 0.87
    },
    {
      "rank_no": 2,
      "stock_code": "000660",
      "stock_name": "SK하이닉스",
      "recommendation": "BUY",
      "reason": "AI 반도체와 고대역폭 메모리 수요 회복 기대가 크다.",
      "confidence": 0.82
    }
  ],
  "data_source": "database"
}
```

## 최신 분석에 사용된 뉴스 조회

요청:

```http
GET /api/analyses/latest/news
```

응답 예시:

```json
{
  "analysis_id": 1,
  "news_articles": [
    {
      "article_id": 2,
      "title": "인터넷 플랫폼 기업, 광고 시장 둔화 우려",
      "summary": "이번 분기 온라인 광고 시장 성장세가 둔화될 수 있다는 전망이 나오고 있다.",
      "url": "https://news.example.com/platform-ad-slowdown",
      "publisher": "예시경제",
      "source": "ls_securities",
      "published_at": "2026-05-09 09:10:00"
    },
    {
      "article_id": 1,
      "title": "AI 반도체 수요 증가세 지속",
      "summary": "AI 서버 투자가 확대되면서 반도체 수요가 증가할 가능성이 제기되고 있다.",
      "url": "https://news.example.com/ai-semiconductor-demand",
      "publisher": "예시경제",
      "source": "ls_securities",
      "published_at": "2026-05-09 09:00:00"
    }
  ],
  "data_source": "database"
}
```
