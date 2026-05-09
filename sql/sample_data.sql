USE stock_prediction_db;

INSERT INTO users (username, email, password_hash)
VALUES
    ('seungbin', 'seungbin@example.com', 'example_hash'),
    ('demo', 'demo@example.com', 'example_hash');

INSERT INTO stocks (stock_code, stock_name, market)
VALUES
    ('005930', 'Samsung Electronics', 'KOSPI'),
    ('000660', 'SK hynix', 'KOSPI'),
    ('035420', 'NAVER', 'KOSPI');

INSERT INTO news_articles (title, summary, url, url_hash, publisher, source, published_at)
VALUES
    (
        'AI semiconductor demand continues to rise',
        'News reports say AI server investment may increase semiconductor demand.',
        'https://news.example.com/ai-semiconductor-demand',
        SHA2('https://news.example.com/ai-semiconductor-demand', 256),
        'Example News',
        'ls_securities',
        '2026-05-09 09:00:00'
    ),
    (
        'Internet platform companies face ad market slowdown',
        'The online advertising market is expected to grow slowly this quarter.',
        'https://news.example.com/platform-ad-slowdown',
        SHA2('https://news.example.com/platform-ad-slowdown', 256),
        'Example News',
        'ls_securities',
        '2026-05-09 09:10:00'
    );

INSERT INTO llm_analysis (user_id, model_name, input_summary, response_json, analyzed_at)
SELECT
    u.user_id,
    'gpt-example',
    'AI semiconductor news is positive. Platform ad market news is weak.',
    JSON_OBJECT(
        'recommendations',
        JSON_ARRAY(
            JSON_OBJECT(
                'stock_code', '005930',
                'stock_name', 'Samsung Electronics',
                'recommendation', 'BUY',
                'reason', 'AI semiconductor demand is positive.',
                'confidence', 0.8700
            ),
            JSON_OBJECT(
                'stock_code', '000660',
                'stock_name', 'SK hynix',
                'recommendation', 'BUY',
                'reason', 'Memory semiconductor demand may improve.',
                'confidence', 0.8200
            )
        )
    ),
    '2026-05-09 10:00:00'
FROM users u
WHERE u.email = 'seungbin@example.com';

INSERT INTO stock_recommendations (analysis_id, stock_id, rank_no, recommendation, reason, confidence)
SELECT a.analysis_id, s.stock_id, 1, 'BUY', 'AI semiconductor demand is positive.', 0.8700
FROM llm_analysis a
JOIN stocks s ON s.stock_code = '005930'
WHERE a.model_name = 'gpt-example';

INSERT INTO stock_recommendations (analysis_id, stock_id, rank_no, recommendation, reason, confidence)
SELECT a.analysis_id, s.stock_id, 2, 'BUY', 'Memory semiconductor demand may improve.', 0.8200
FROM llm_analysis a
JOIN stocks s ON s.stock_code = '000660'
WHERE a.model_name = 'gpt-example';
