# 테이블별 컬럼 설명

이 문서는 `stock_prediction_db` 데이터베이스의 각 테이블이 어떤 데이터를 저장하는지 설명한다.
팀원이 API, AI, UI 코드를 작성할 때 어떤 컬럼에 어떤 값을 넣어야 하는지 확인하는 용도로 사용한다.

## 1. users

사용자 회원 정보를 저장하는 테이블이다.

| 컬럼명 | 설명 |
| --- | --- |
| user_id | 사용자 고유 번호 |
| username | 로그인 아이디 |
| email | 사용자 이메일 |
| password_hash | 암호화된 비밀번호 |
| full_name | 사용자 실제 이름 |
| phone_number | 사용자 전화번호 |
| created_at | 사용자 정보가 처음 생성된 시간 |
| updated_at | 사용자 정보가 마지막으로 수정된 시간 |

## 2. stocks

주식 종목의 기본 정보를 저장하는 테이블이다.

| 컬럼명 | 설명 |
| --- | --- |
| stock_id | 종목 고유 번호 |
| stock_code | 종목 코드, 예: 삼성전자 005930 |
| stock_name | 종목명, 예: 삼성전자 |
| market | 주식 시장 구분, 예: KOSPI, KOSDAQ, NASDAQ |
| currency | 거래 통화, 예: KRW, USD |
| sector | 업종, 예: 반도체, 인터넷 서비스 |
| created_at | 종목 정보가 처음 생성된 시간 |
| updated_at | 종목 정보가 마지막으로 수정된 시간 |

## 3. user_holdings

사용자가 보유한 주식 정보를 저장하는 테이블이다.

| 컬럼명 | 설명 |
| --- | --- |
| holding_id | 보유 주식 고유 번호 |
| user_id | 어떤 사용자의 보유 주식인지 나타내는 사용자 번호 |
| stock_id | 어떤 종목을 보유 중인지 나타내는 종목 번호 |
| quantity | 보유 수량 |
| average_buy_price | 평균 매수가 |
| buy_date | 매수일 |
| memo | 사용자가 남긴 메모 |
| created_at | 보유 주식 정보가 처음 생성된 시간 |
| updated_at | 보유 주식 정보가 마지막으로 수정된 시간 |

## 4. stock_prices

종목별 현재가와 시세 정보를 저장하는 테이블이다.

| 컬럼명 | 설명 |
| --- | --- |
| price_id | 시세 데이터 고유 번호 |
| stock_id | 어떤 종목의 시세인지 나타내는 종목 번호 |
| current_price | 현재가 |
| open_price | 시가, 장 시작 가격 |
| high_price | 고가, 해당 시점 기준 가장 높은 가격 |
| low_price | 저가, 해당 시점 기준 가장 낮은 가격 |
| close_price | 종가 |
| trading_volume | 거래량 |
| source | 시세 데이터를 가져온 출처, 예: API 이름 |
| collected_at | 시세 데이터를 수집한 시간 |
| created_at | 시세 데이터가 처음 저장된 시간 |
| updated_at | 시세 데이터가 마지막으로 수정된 시간 |

## 5. news_articles

종목 관련 뉴스 기사 정보를 저장하는 테이블이다.

| 컬럼명 | 설명 |
| --- | --- |
| article_id | 뉴스 기사 고유 번호 |
| stock_id | 어떤 종목과 관련된 뉴스인지 나타내는 종목 번호 |
| title | 뉴스 제목 |
| summary | 뉴스 요약문 |
| url | 뉴스 기사 링크 |
| url_hash | URL 중복 저장을 막기 위한 해시값 |
| publisher | 언론사 또는 발행처 |
| source | 뉴스 데이터를 가져온 출처, 예: Google News RSS |
| language | 뉴스 언어, 예: ko, en |
| published_at | 뉴스가 발행된 시간 |
| collected_at | 뉴스 데이터를 수집한 시간 |
| created_at | 뉴스 데이터가 처음 저장된 시간 |
| updated_at | 뉴스 데이터가 마지막으로 수정된 시간 |

## 6. sentiment_analysis

뉴스 기사에 대한 감성 분석 결과를 저장하는 테이블이다.

| 컬럼명 | 설명 |
| --- | --- |
| sentiment_id | 감성 분석 결과 고유 번호 |
| article_id | 어떤 뉴스 기사에 대한 분석인지 나타내는 기사 번호 |
| sentiment_label | 감성 분류 결과, Positive, Neutral, Negative |
| sentiment_score | 감성 점수, Positive는 1, Neutral은 0, Negative는 -1 |
| confidence | 감성 분석 신뢰도 |
| analyzed_model | 감성 분석에 사용한 모델 또는 방식 이름 |
| analyzed_at | 감성 분석을 수행한 시간 |
| created_at | 감성 분석 결과가 처음 저장된 시간 |
| updated_at | 감성 분석 결과가 마지막으로 수정된 시간 |

## 7. stock_predictions

뉴스 감성 분석 결과 등을 바탕으로 계산한 주가 예측 결과를 저장하는 테이블이다.

| 컬럼명 | 설명 |
| --- | --- |
| prediction_id | 예측 고유 번호 |
| stock_id | 어떤 종목에 대한 예측인지 나타내는 종목 번호 |
| prediction_date | 예측 대상 날짜 |
| prediction_direction | 예측 방향, UP, DOWN, NEUTRAL |
| predicted_change_rate | 예상 변동률 |
| predicted_price | 예상 가격 |
| sentiment_avg_score | 뉴스 감성 평균 점수 |
| confidence | 예측 신뢰도 |
| basis_start_at | 예측에 사용한 데이터의 시작 시간 |
| basis_end_at | 예측에 사용한 데이터의 종료 시간 |
| model_name | 예측 모델 이름 |
| model_version | 예측 모델 버전 |
| created_at | 예측 결과가 처음 저장된 시간 |
| updated_at | 예측 결과가 마지막으로 수정된 시간 |

## 8. user_reports

사용자별 최종 투자 리포트를 저장하는 테이블이다.

| 컬럼명 | 설명 |
| --- | --- |
| report_id | 리포트 고유 번호 |
| user_id | 어떤 사용자의 리포트인지 나타내는 사용자 번호 |
| stock_id | 어떤 종목에 대한 리포트인지 나타내는 종목 번호 |
| prediction_id | 리포트 작성에 사용한 예측 결과 번호 |
| report_title | 리포트 제목 |
| report_content | 리포트 본문 내용 |
| profit_rate | 사용자의 현재 수익률 |
| profit_amount | 사용자의 현재 손익 금액 |
| recommendation | 추천 의견, BUY, HOLD, SELL, WATCH |
| generated_at | 리포트가 생성된 시간 |
| created_at | 리포트가 처음 저장된 시간 |
| updated_at | 리포트가 마지막으로 수정된 시간 |

## 팀원별 사용 예시

### API/AI 담당

- 뉴스 수집 결과는 `news_articles`에 저장한다.
- 감성 분석 결과는 `sentiment_analysis`에 저장한다.
- 예측 결과는 `stock_predictions`에 저장한다.

### UI 담당

- 사용자 보유 주식 화면은 `users`, `user_holdings`, `stocks`, `stock_prices`를 조인해서 보여준다.
- 뉴스 화면은 `stocks`, `news_articles`, `sentiment_analysis`를 조인해서 보여준다.
- 리포트 화면은 `user_reports`, `stocks`, `stock_predictions`를 조인해서 보여준다.

### DB 담당

- 테이블 생성 SQL은 `sql/schema.sql`에서 관리한다.
- 테스트 데이터는 `sql/sample_data.sql`에서 관리한다.
- Python DB 연결 함수는 `src/db/database.py`에서 관리한다.
