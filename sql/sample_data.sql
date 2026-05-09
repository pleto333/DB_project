USE stock_prediction_db;

INSERT INTO users (username, email, password_hash, full_name, phone_number)
VALUES
    ('seungbin', 'seungbin@example.com', 'example_hash_please_replace', '유승빈', '010-1234-5678'),
    ('daehyun', 'daehyun@example.com', 'example_hash_please_replace', '이대현', '010-2222-3333')
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    full_name = VALUES(full_name),
    phone_number = VALUES(phone_number);

INSERT INTO stocks (stock_code, stock_name, market, currency, sector)
VALUES
    ('005930', '삼성전자', 'KOSPI', 'KRW', '반도체'),
    ('035420', 'NAVER', 'KOSPI', 'KRW', '인터넷 서비스')
ON DUPLICATE KEY UPDATE
    stock_name = VALUES(stock_name),
    market = VALUES(market),
    currency = VALUES(currency),
    sector = VALUES(sector);

INSERT INTO user_holdings (user_id, stock_id, quantity, average_buy_price, buy_date, memo)
SELECT u.user_id, s.stock_id, 10, 72000, '2026-04-01', '중장기 보유 예정'
FROM users u
JOIN stocks s ON s.stock_code = '005930'
WHERE u.email = 'seungbin@example.com'
ON DUPLICATE KEY UPDATE
    quantity = VALUES(quantity),
    average_buy_price = VALUES(average_buy_price),
    buy_date = VALUES(buy_date),
    memo = VALUES(memo);

INSERT INTO user_holdings (user_id, stock_id, quantity, average_buy_price, buy_date, memo)
SELECT u.user_id, s.stock_id, 5, 190000, '2026-04-10', '뉴스 감성 추적 대상'
FROM users u
JOIN stocks s ON s.stock_code = '035420'
WHERE u.email = 'seungbin@example.com'
ON DUPLICATE KEY UPDATE
    quantity = VALUES(quantity),
    average_buy_price = VALUES(average_buy_price),
    buy_date = VALUES(buy_date),
    memo = VALUES(memo);

INSERT INTO stock_prices (
    stock_id, current_price, open_price, high_price, low_price, close_price,
    trading_volume, source, collected_at
)
SELECT s.stock_id, 74500, 73800, 74800, 73500, 74500, 12450000, 'sample_api', '2026-05-09 09:30:00'
FROM stocks s
WHERE s.stock_code = '005930'
ON DUPLICATE KEY UPDATE
    current_price = VALUES(current_price),
    open_price = VALUES(open_price),
    high_price = VALUES(high_price),
    low_price = VALUES(low_price),
    close_price = VALUES(close_price),
    trading_volume = VALUES(trading_volume);

INSERT INTO stock_prices (
    stock_id, current_price, open_price, high_price, low_price, close_price,
    trading_volume, source, collected_at
)
SELECT s.stock_id, 184000, 186000, 187500, 183000, 184000, 2310000, 'sample_api', '2026-05-09 09:30:00'
FROM stocks s
WHERE s.stock_code = '035420'
ON DUPLICATE KEY UPDATE
    current_price = VALUES(current_price),
    open_price = VALUES(open_price),
    high_price = VALUES(high_price),
    low_price = VALUES(low_price),
    close_price = VALUES(close_price),
    trading_volume = VALUES(trading_volume);

INSERT INTO news_articles (
    stock_id, title, summary, url, url_hash, publisher, source, language, published_at, collected_at
)
SELECT
    s.stock_id,
    '삼성전자, AI 반도체 수요 증가 기대',
    'AI 서버 투자 확대가 메모리 반도체 수요 회복으로 이어질 수 있다는 분석이 나왔다.',
    'https://news.example.com/samsung-ai-chip',
    SHA2('https://news.example.com/samsung-ai-chip', 256),
    'Example News',
    'google_news_rss',
    'ko',
    '2026-05-09 08:00:00',
    '2026-05-09 09:00:00'
FROM stocks s
WHERE s.stock_code = '005930'
ON DUPLICATE KEY UPDATE
    title = VALUES(title),
    summary = VALUES(summary),
    publisher = VALUES(publisher),
    published_at = VALUES(published_at),
    collected_at = VALUES(collected_at);

INSERT INTO news_articles (
    stock_id, title, summary, url, url_hash, publisher, source, language, published_at, collected_at
)
SELECT
    s.stock_id,
    'NAVER, 광고 시장 둔화 우려',
    '경기 둔화로 온라인 광고 성장률이 낮아질 수 있다는 전망이 제기됐다.',
    'https://news.example.com/naver-ad-market',
    SHA2('https://news.example.com/naver-ad-market', 256),
    'Example News',
    'google_news_rss',
    'ko',
    '2026-05-09 08:20:00',
    '2026-05-09 09:00:00'
FROM stocks s
WHERE s.stock_code = '035420'
ON DUPLICATE KEY UPDATE
    title = VALUES(title),
    summary = VALUES(summary),
    publisher = VALUES(publisher),
    published_at = VALUES(published_at),
    collected_at = VALUES(collected_at);

INSERT INTO sentiment_analysis (article_id, sentiment_label, sentiment_score, confidence, analyzed_model, analyzed_at)
SELECT article_id, 'Positive', 1, 0.8700, 'rule_based_v1', '2026-05-09 09:10:00'
FROM news_articles
WHERE url_hash = SHA2('https://news.example.com/samsung-ai-chip', 256)
ON DUPLICATE KEY UPDATE
    sentiment_label = VALUES(sentiment_label),
    sentiment_score = VALUES(sentiment_score),
    confidence = VALUES(confidence),
    analyzed_model = VALUES(analyzed_model),
    analyzed_at = VALUES(analyzed_at);

INSERT INTO sentiment_analysis (article_id, sentiment_label, sentiment_score, confidence, analyzed_model, analyzed_at)
SELECT article_id, 'Negative', -1, 0.7800, 'rule_based_v1', '2026-05-09 09:10:00'
FROM news_articles
WHERE url_hash = SHA2('https://news.example.com/naver-ad-market', 256)
ON DUPLICATE KEY UPDATE
    sentiment_label = VALUES(sentiment_label),
    sentiment_score = VALUES(sentiment_score),
    confidence = VALUES(confidence),
    analyzed_model = VALUES(analyzed_model),
    analyzed_at = VALUES(analyzed_at);

INSERT INTO stock_predictions (
    stock_id, prediction_date, prediction_direction, predicted_change_rate, predicted_price,
    sentiment_avg_score, confidence, basis_start_at, basis_end_at, model_name, model_version
)
SELECT
    s.stock_id,
    '2026-05-10',
    'UP',
    1.5000,
    75617.5000,
    1.0000,
    0.8200,
    '2026-05-09 00:00:00',
    '2026-05-09 23:59:59',
    'sentiment_average_model',
    'v1'
FROM stocks s
WHERE s.stock_code = '005930'
ON DUPLICATE KEY UPDATE
    prediction_direction = VALUES(prediction_direction),
    predicted_change_rate = VALUES(predicted_change_rate),
    predicted_price = VALUES(predicted_price),
    sentiment_avg_score = VALUES(sentiment_avg_score),
    confidence = VALUES(confidence),
    basis_start_at = VALUES(basis_start_at),
    basis_end_at = VALUES(basis_end_at);

INSERT INTO stock_predictions (
    stock_id, prediction_date, prediction_direction, predicted_change_rate, predicted_price,
    sentiment_avg_score, confidence, basis_start_at, basis_end_at, model_name, model_version
)
SELECT
    s.stock_id,
    '2026-05-10',
    'DOWN',
    -1.2000,
    181792.0000,
    -1.0000,
    0.7300,
    '2026-05-09 00:00:00',
    '2026-05-09 23:59:59',
    'sentiment_average_model',
    'v1'
FROM stocks s
WHERE s.stock_code = '035420'
ON DUPLICATE KEY UPDATE
    prediction_direction = VALUES(prediction_direction),
    predicted_change_rate = VALUES(predicted_change_rate),
    predicted_price = VALUES(predicted_price),
    sentiment_avg_score = VALUES(sentiment_avg_score),
    confidence = VALUES(confidence),
    basis_start_at = VALUES(basis_start_at),
    basis_end_at = VALUES(basis_end_at);

INSERT INTO user_reports (
    user_id, stock_id, prediction_id, report_title, report_content,
    profit_rate, profit_amount, recommendation, generated_at
)
SELECT
    u.user_id,
    s.stock_id,
    p.prediction_id,
    '삼성전자 개인 맞춤 리포트',
    '현재 수익률은 약 3.47%이며, 최근 뉴스 감성은 긍정적이다. 단기 예측 방향은 상승으로 계산되었다.',
    3.4722,
    25000.0000,
    'HOLD',
    '2026-05-09 10:00:00'
FROM users u
JOIN stocks s ON s.stock_code = '005930'
LEFT JOIN stock_predictions p
    ON p.stock_id = s.stock_id
    AND p.prediction_date = '2026-05-10'
    AND p.model_name = 'sentiment_average_model'
    AND p.model_version = 'v1'
WHERE u.email = 'seungbin@example.com'
ON DUPLICATE KEY UPDATE
    prediction_id = VALUES(prediction_id),
    report_title = VALUES(report_title),
    report_content = VALUES(report_content),
    profit_rate = VALUES(profit_rate),
    profit_amount = VALUES(profit_amount),
    recommendation = VALUES(recommendation);

INSERT INTO user_reports (
    user_id, stock_id, prediction_id, report_title, report_content,
    profit_rate, profit_amount, recommendation, generated_at
)
SELECT
    u.user_id,
    s.stock_id,
    p.prediction_id,
    'NAVER 개인 맞춤 리포트',
    '현재 수익률은 약 -3.16%이며, 최근 뉴스 감성은 부정적이다. 추가 매수보다는 관망이 적절하다.',
    -3.1579,
    -30000.0000,
    'WATCH',
    '2026-05-09 10:00:00'
FROM users u
JOIN stocks s ON s.stock_code = '035420'
LEFT JOIN stock_predictions p
    ON p.stock_id = s.stock_id
    AND p.prediction_date = '2026-05-10'
    AND p.model_name = 'sentiment_average_model'
    AND p.model_version = 'v1'
WHERE u.email = 'seungbin@example.com'
ON DUPLICATE KEY UPDATE
    prediction_id = VALUES(prediction_id),
    report_title = VALUES(report_title),
    report_content = VALUES(report_content),
    profit_rate = VALUES(profit_rate),
    profit_amount = VALUES(profit_amount),
    recommendation = VALUES(recommendation);
