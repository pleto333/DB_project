# 주식 가격예측 시스템 DB 설계 정리

## 1. PPT 기반 프로젝트 이해

이 프로젝트는 사용자가 보유 중인 주식에 대해 현재가, 관련 뉴스, 뉴스 감성 분석 결과를 결합하여 개인 맞춤형 투자 리포트를 제공하는 시스템이다.

주요 흐름은 다음과 같다.

1. 사용자가 회원가입/로그인을 한다.
2. 사용자가 보유 종목, 보유 수량, 평균 매수가, 매수일을 등록한다.
3. 외부 주식 시세 API에서 현재가를 수집한다.
4. 뉴스 API 또는 Google News RSS에서 종목 관련 뉴스를 수집한다.
5. Python에서 뉴스 제목/요약문을 감성 분석한다.
6. 감성 평균 점수를 바탕으로 주가 방향 또는 예상 변동률을 계산한다.
7. 사용자 매수가, 현재가, 수익률, 감성 분석, 예측 결과를 종합해 최종 리포트를 생성한다.

## 2. 테이블 설계 이유

| 테이블 | 역할 | 설계 이유 |
| --- | --- | --- |
| users | 사용자 계정 정보 저장 | 사용자별 보유 종목과 리포트를 구분하기 위한 기준 테이블 |
| stocks | 종목 기본 정보 저장 | 종목명/종목코드를 한 곳에서 관리해 중복 저장 방지 |
| user_holdings | 사용자 보유 주식 저장 | users와 stocks를 연결하는 테이블, 사용자별 수량/평균 매수가 관리 |
| stock_prices | 주식 시세 이력 저장 | 현재가를 시간별로 저장해 최신가 조회와 과거 분석 가능 |
| news_articles | 뉴스 기사 저장 | 종목별 뉴스 원문 메타데이터 관리 |
| sentiment_analysis | 뉴스 감성 분석 결과 저장 | 뉴스와 분석 결과를 분리해 분석 모델 변경/재분석에 대응 |
| stock_predictions | 주가 예측 결과 저장 | 종목별 예측 방향, 예상 변동률, 예측 가격 관리 |
| user_reports | 사용자별 최종 리포트 저장 | 개인 보유 정보와 예측 결과를 종합한 결과를 이력으로 보존 |

## 3. 텍스트 ERD

```text
users (1) ── (N) user_holdings
stocks (1) ── (N) user_holdings

stocks (1) ── (N) stock_prices

stocks (1) ── (N) news_articles
news_articles (1) ── (1) sentiment_analysis

stocks (1) ── (N) stock_predictions

users (1) ── (N) user_reports
stocks (1) ── (N) user_reports
stock_predictions (1) ── (N) user_reports
```

관계 설명:

- 한 명의 사용자는 여러 종목을 보유할 수 있다.
- 하나의 종목은 여러 사용자가 보유할 수 있다.
- 하나의 종목에는 시간별 시세 데이터가 여러 개 저장된다.
- 하나의 종목에는 여러 뉴스 기사가 연결된다.
- 하나의 뉴스 기사는 하나의 감성 분석 결과를 가진다.
- 하나의 종목에는 날짜별 예측 결과가 여러 개 저장된다.
- 하나의 사용자는 여러 최종 리포트를 받을 수 있다.

## 4. 정규화 포인트

- 종목명과 종목코드는 stocks에 한 번만 저장하고, 다른 테이블은 stock_id로 참조한다.
- 뉴스 기사와 감성 분석 결과를 분리해 원문 뉴스 중복 저장을 줄인다.
- 시세 데이터는 stock_prices에 이력 형태로 저장해 같은 종목의 여러 수집 시점을 관리한다.
- user_reports는 생성 당시의 수익률과 추천 결과를 저장해 리포트 이력을 보존한다.

## 5. 주요 인덱스

| 인덱스 대상 | 목적 |
| --- | --- |
| users.email, users.username | 로그인/중복 가입 확인 |
| stocks.stock_code | 종목코드로 빠른 종목 조회 |
| user_holdings.user_id | 사용자별 보유 주식 조회 |
| stock_prices.stock_id, collected_at | 종목별 최신 시세 조회 |
| news_articles.stock_id, published_at | 종목별 최신 뉴스 조회 |
| sentiment_analysis.article_id | 뉴스별 감성 분석 결과 조회 |
| stock_predictions.stock_id, prediction_date | 종목별 예측 결과 조회 |
| user_reports.user_id, generated_at | 사용자별 최신 리포트 조회 |

## 6. 실행 순서

```powershell
mysql -u root -p < sql/schema.sql
mysql -u root -p stock_prediction_db < sql/sample_data.sql
```

Python 패키지 설치:

```powershell
pip install -r requirements.txt
```

환경변수 예시:

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
