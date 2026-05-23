# 실제 뉴스 API 연동 가이드

이 문서는 API 담당자가 LS증권 등 실제 뉴스 API를 프로젝트에 붙일 때 참고하기 위한 가이드입니다. 현재 프로젝트는 샘플 데이터로 동작하지만, 실제 연동 시에는 아래 흐름대로 `news_articles` 테이블에 뉴스 원본을 저장하고, 저장된 뉴스 ID를 LLM 분석 단계로 넘기면 됩니다.

## 전체 연결 흐름

```text
1. LS증권 API 인증키 준비
2. 뉴스 API 호출
3. 응답 데이터를 우리 DB 컬럼에 맞게 변환
4. news_articles 테이블에 저장
5. 저장된 article_id 목록을 LLM 담당 코드에 전달
6. LLM 분석 결과를 llm_analysis, stock_recommendations에 저장
7. Vue 화면은 FastAPI 조회 API를 통해 결과 표시
```

API 담당자가 우선 맡을 부분은 1번부터 4번까지입니다. 5번부터는 LLM/AI 담당과 연결하면 됩니다.

## 관련 파일

- `src/db/database.py`: DB 저장 함수가 이미 들어 있는 파일
- `sql/schema.sql`: 실제 저장되는 테이블 구조
- `app.py`: 프론트엔드가 조회하는 FastAPI 서버
- `docs/frontend_handoff.md`: 프론트엔드 담당자 인수인계 문서

## 환경 변수 예시

API 키는 코드에 직접 쓰지 말고 환경 변수로 관리하는 것이 좋습니다.

```powershell
$env:LS_APP_KEY="발급받은_APP_KEY"
$env:LS_APP_SECRET="발급받은_APP_SECRET"
$env:LS_ACCESS_TOKEN="발급받은_ACCESS_TOKEN"
$env:LS_NEWS_ENDPOINT="뉴스_API_주소"
```

인증 방식이 토큰 발급형이면 `LS_APP_KEY`, `LS_APP_SECRET`으로 먼저 토큰을 받은 뒤 `LS_ACCESS_TOKEN`처럼 저장해서 뉴스 요청에 사용하면 됩니다.

## API 응답과 DB 컬럼 매핑

실제 API 응답 필드명은 LS증권 문서 기준으로 확인해야 합니다. 프로젝트 DB에는 아래 형태로 맞춰 저장하면 됩니다.

| API 의미 | DB 컬럼 | 설명 |
| --- | --- | --- |
| 뉴스 제목 | `news_articles.title` | 필수 |
| 뉴스 요약 또는 본문 일부 | `news_articles.summary` | 없으면 `NULL` 가능 |
| 뉴스 원문 URL | `news_articles.url` | 필수 |
| 언론사 | `news_articles.publisher` | 없으면 `NULL` 가능 |
| 데이터 출처 | `news_articles.source` | LS증권이면 `ls_securities` |
| 뉴스 발행 시각 | `news_articles.published_at` | `YYYY-MM-DD HH:MM:SS` 형식 권장 |
| 수집 시각 | `news_articles.collected_at` | DB에서 자동 저장 |

`url_hash`는 `save_news_article()` 함수 안에서 자동 생성됩니다. 같은 URL을 다시 저장하면 중복 INSERT가 아니라 기존 뉴스를 갱신하도록 되어 있습니다.

## 저장 함수 사용 예시

`src/db/database.py`에 이미 `save_news_article()` 함수가 있습니다. 실제 API 담당자는 API 응답을 이 함수에 맞게 변환하면 됩니다.

```python
from src.db.database import save_news_article

article_id = save_news_article(
    title="반도체 수출 회복세 지속",
    summary="AI 서버 수요 증가로 국내 반도체 업종 투자 심리가 개선되고 있다.",
    url="https://example.com/news/123",
    publisher="예시경제",
    source="ls_securities",
    published_at="2026-05-23 09:30:00",
)

print(article_id)
```

반환되는 `article_id`는 LLM 분석 단계에서 어떤 뉴스를 분석했는지 연결할 때 사용합니다.

## 뉴스 수집 코드 뼈대

아래 코드는 실제 LS증권 API 문서에 맞춰 URL, 헤더, 파라미터만 바꾸면 되는 형태입니다.

```python
import os
import requests

from src.db.database import save_news_article


def fetch_news_from_ls() -> list[dict]:
    endpoint = os.getenv("LS_NEWS_ENDPOINT")
    access_token = os.getenv("LS_ACCESS_TOKEN")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    params = {
        "page": 1,
        "size": 20,
    }

    response = requests.get(endpoint, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    payload = response.json()

    # TODO: 실제 LS증권 응답 구조에 맞춰 수정
    return payload["news"]


def collect_and_save_news() -> list[int]:
    article_ids = []

    for item in fetch_news_from_ls():
        article_id = save_news_article(
            title=item["title"],
            summary=item.get("summary"),
            url=item["url"],
            publisher=item.get("publisher"),
            source="ls_securities",
            published_at=item.get("published_at"),
        )
        article_ids.append(article_id)

    return article_ids
```

이 코드를 실제로 사용하려면 `requirements.txt`에 `requests`를 추가하거나, 팀에서 선호하는 HTTP 라이브러리인 `httpx` 등을 사용하면 됩니다.

## LLM 담당자에게 넘길 데이터

뉴스를 저장한 뒤에는 `article_id` 목록을 LLM 담당 코드로 넘기면 됩니다.

```python
article_ids = collect_and_save_news()
```

LLM 담당자는 이 `article_ids`에 해당하는 뉴스 제목과 요약을 가져와 LLM에 전달하고, 분석이 끝나면 다음 순서로 저장하면 됩니다.

```text
1. save_llm_analysis()로 LLM 원본 응답 저장
2. link_analysis_news_articles()로 분석 결과와 뉴스 연결
3. add_stock()으로 추천 종목 저장 또는 기존 종목 ID 조회
4. save_stock_recommendation()으로 추천 결과 저장
```

## 실제 연동 시 확인할 것

- API 응답의 날짜 형식이 DB의 `DATETIME`에 들어갈 수 있는지 확인
- 같은 뉴스가 반복 수집될 수 있으므로 URL 중복 처리 확인
- 뉴스 본문 전체를 저장할지, 요약만 저장할지 결정
- API 호출 실패 시 바로 중단할지, 재시도할지 결정
- 하루에 몇 번 수집할지 결정
- 무료 API 호출 제한이 있다면 테스트 횟수 제한
- API 키가 GitHub에 올라가지 않도록 `.env` 또는 환경 변수 사용

## 팀원 작업 체크리스트

- [ ] LS증권 API 신청 완료
- [ ] 인증 방식 확인
- [ ] 뉴스 조회 엔드포인트 확인
- [ ] 실제 응답 JSON 샘플 저장
- [ ] 응답 필드를 `news_articles` 컬럼에 매핑
- [ ] `save_news_article()`로 DB 저장 테스트
- [ ] 중복 뉴스 저장 테스트
- [ ] 저장된 뉴스가 `scripts/inspect_database.py`에서 보이는지 확인
- [ ] LLM 담당자에게 `article_id` 목록 전달 방식 공유

