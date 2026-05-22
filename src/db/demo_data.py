from __future__ import annotations

from typing import Any


DEMO_ANALYSIS_ID = 1


DEMO_RECOMMENDATIONS: dict[str, Any] = {
    "analysis_id": DEMO_ANALYSIS_ID,
    "recommendations": [
        {
            "rank_no": 1,
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "recommendation": "BUY",
            "reason": "AI 서버 투자 확대로 메모리와 반도체 수요 증가가 기대된다.",
            "confidence": 0.87,
        },
        {
            "rank_no": 2,
            "stock_code": "000660",
            "stock_name": "SK하이닉스",
            "recommendation": "BUY",
            "reason": "AI 반도체와 고대역폭 메모리 수요 회복 기대가 크다.",
            "confidence": 0.82,
        },
    ],
}


DEMO_NEWS_ARTICLES: dict[str, Any] = {
    "analysis_id": DEMO_ANALYSIS_ID,
    "news_articles": [
        {
            "article_id": 1,
            "title": "AI 반도체 수요 증가세 지속",
            "summary": "AI 서버 투자가 확대되면서 반도체 수요가 증가할 가능성이 제기되고 있다.",
            "url": "https://news.example.com/ai-semiconductor-demand",
            "publisher": "예시경제",
            "source": "ls_securities",
            "published_at": "2026-05-09 09:00:00",
        },
        {
            "article_id": 2,
            "title": "인터넷 플랫폼 기업, 광고 시장 둔화 우려",
            "summary": "이번 분기 온라인 광고 시장 성장세가 둔화될 수 있다는 전망이 나오고 있다.",
            "url": "https://news.example.com/platform-ad-slowdown",
            "publisher": "예시경제",
            "source": "ls_securities",
            "published_at": "2026-05-09 09:10:00",
        },
    ],
}


DEMO_ANALYSES: dict[str, Any] = {
    "analyses": [
        {
            "analysis_id": DEMO_ANALYSIS_ID,
            "model_name": "gpt-example",
            "input_summary": "AI 반도체 수요 증가는 반도체 대형주에 긍정적이다.",
            "theme": "반도체",
            "analyzed_at": "2026-05-09 10:00:00",
            "recommendation_count": 2,
            "news_count": 2,
        }
    ]
}


def demo_analyses() -> dict[str, Any]:
    return dict(DEMO_ANALYSES)


def demo_recommendations(analysis_id: int | None = None) -> dict[str, Any]:
    result = dict(DEMO_RECOMMENDATIONS)
    result["analysis_id"] = analysis_id or DEMO_ANALYSIS_ID
    return result


def demo_news_articles(analysis_id: int | None = None) -> dict[str, Any]:
    result = dict(DEMO_NEWS_ARTICLES)
    result["analysis_id"] = analysis_id or DEMO_ANALYSIS_ID
    return result
