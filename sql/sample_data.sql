USE stock_prediction_db;

INSERT INTO users (username, email, password_hash)
VALUES
    ('seungbin', 'seungbin@example.com', 'example_hash'),
    ('demo', 'demo@example.com', 'example_hash');

INSERT INTO stocks (stock_code, stock_name, market)
VALUES
    ('005930', '삼성전자', 'KOSPI'),
    ('000660', 'SK하이닉스', 'KOSPI'),
    ('035420', 'NAVER', 'KOSPI'),
    ('035720', '카카오', 'KOSPI'),
    ('373220', 'LG에너지솔루션', 'KOSPI'),
    ('006400', '삼성SDI', 'KOSPI'),
    ('003670', '포스코퓨처엠', 'KOSPI');

INSERT INTO news_articles (title, summary, url, url_hash, publisher, source, published_at)
VALUES
    (
        'AI 반도체 수요 증가세 지속',
        'AI 서버 투자가 확대되면서 메모리 반도체 수요가 증가할 가능성이 제기되고 있다.',
        'https://news.example.com/ai-semiconductor-demand',
        SHA2('https://news.example.com/ai-semiconductor-demand', 256),
        '예시경제',
        'ls_securities',
        '2026-05-09 09:00:00'
    ),
    (
        'HBM 공급 부족 우려 확대',
        '고대역폭 메모리 수요가 빠르게 늘면서 주요 반도체 기업의 실적 개선 기대가 커지고 있다.',
        'https://news.example.com/hbm-supply-shortage',
        SHA2('https://news.example.com/hbm-supply-shortage', 256),
        '예시증권',
        'ls_securities',
        '2026-05-09 09:20:00'
    ),
    (
        '반도체 수출 회복세 확인',
        '국내 반도체 수출이 회복 흐름을 보이며 업황 개선 기대가 이어지고 있다.',
        'https://news.example.com/semiconductor-export-recovery',
        SHA2('https://news.example.com/semiconductor-export-recovery', 256),
        '마켓데일리',
        'ls_securities',
        '2026-05-09 09:40:00'
    ),
    (
        '전기차 판매 회복 기대',
        '하반기 전기차 판매량 회복 전망이 나오면서 배터리 업종 투자 심리가 개선되고 있다.',
        'https://news.example.com/ev-sales-recovery',
        SHA2('https://news.example.com/ev-sales-recovery', 256),
        '예시경제',
        'ls_securities',
        '2026-05-10 10:00:00'
    ),
    (
        '배터리 소재 가격 안정세',
        '리튬 등 주요 배터리 소재 가격이 안정되면서 배터리 기업의 수익성 개선 기대가 나오고 있다.',
        'https://news.example.com/battery-material-price',
        SHA2('https://news.example.com/battery-material-price', 256),
        '예시증권',
        'ls_securities',
        '2026-05-10 10:20:00'
    ),
    (
        '북미 배터리 공장 투자 확대',
        '국내 배터리 기업들이 북미 생산 거점을 확대하며 중장기 성장 기반을 강화하고 있다.',
        'https://news.example.com/north-america-battery-investment',
        SHA2('https://news.example.com/north-america-battery-investment', 256),
        '마켓데일리',
        'ls_securities',
        '2026-05-10 10:40:00'
    ),
    (
        '인터넷 플랫폼 기업, 광고 시장 둔화 우려',
        '이번 분기 온라인 광고 시장 성장세가 둔화될 수 있다는 전망이 나오고 있다.',
        'https://news.example.com/platform-ad-slowdown',
        SHA2('https://news.example.com/platform-ad-slowdown', 256),
        '예시경제',
        'ls_securities',
        '2026-05-11 11:00:00'
    ),
    (
        '커머스 경쟁 심화로 플랫폼 비용 부담 증가',
        '플랫폼 기업들의 커머스 경쟁이 심화되면서 마케팅 비용 증가가 실적 부담 요인으로 거론된다.',
        'https://news.example.com/platform-commerce-competition',
        SHA2('https://news.example.com/platform-commerce-competition', 256),
        '예시증권',
        'ls_securities',
        '2026-05-11 11:20:00'
    );

INSERT INTO llm_analysis (user_id, model_name, input_summary, response_json, analyzed_at)
SELECT
    u.user_id,
    'gpt-example',
    'AI 반도체 수요, HBM 공급 부족, 반도체 수출 회복 뉴스는 반도체 대형주에 긍정적이다.',
    JSON_OBJECT(
        'theme',
        '반도체',
        'recommendations',
        JSON_ARRAY(
            JSON_OBJECT(
                'stock_code', '005930',
                'stock_name', '삼성전자',
                'recommendation', 'BUY',
                'reason', 'AI 서버 투자 확대로 메모리와 반도체 수요 증가가 기대된다.',
                'confidence', 0.8700
            ),
            JSON_OBJECT(
                'stock_code', '000660',
                'stock_name', 'SK하이닉스',
                'recommendation', 'BUY',
                'reason', 'HBM 수요 확대와 메모리 업황 회복 기대가 크다.',
                'confidence', 0.8400
            )
        )
    ),
    '2026-05-09 10:00:00'
FROM users u
WHERE u.email = 'seungbin@example.com';

INSERT INTO llm_analysis (user_id, model_name, input_summary, response_json, analyzed_at)
SELECT
    u.user_id,
    'gpt-example',
    '전기차 판매 회복, 배터리 소재 가격 안정, 북미 공장 투자 확대 뉴스는 배터리 업종에 긍정적이다.',
    JSON_OBJECT(
        'theme',
        '2차전지',
        'recommendations',
        JSON_ARRAY(
            JSON_OBJECT(
                'stock_code', '373220',
                'stock_name', 'LG에너지솔루션',
                'recommendation', 'BUY',
                'reason', '전기차 수요 회복과 북미 생산 확대에 따른 성장 기대가 있다.',
                'confidence', 0.8600
            ),
            JSON_OBJECT(
                'stock_code', '006400',
                'stock_name', '삼성SDI',
                'recommendation', 'BUY',
                'reason', '고부가 배터리 중심의 수익성 개선 가능성이 있다.',
                'confidence', 0.8000
            ),
            JSON_OBJECT(
                'stock_code', '003670',
                'stock_name', '포스코퓨처엠',
                'recommendation', 'WATCH',
                'reason', '소재 가격 안정은 긍정적이지만 업황 회복 확인이 더 필요하다.',
                'confidence', 0.6900
            )
        )
    ),
    '2026-05-12 11:00:00'
FROM users u
WHERE u.email = 'seungbin@example.com';

INSERT INTO llm_analysis (user_id, model_name, input_summary, response_json, analyzed_at)
SELECT
    u.user_id,
    'gpt-example',
    '광고 시장 둔화와 커머스 경쟁 심화 뉴스는 플랫폼 업종에 단기 부담으로 작용할 수 있다.',
    JSON_OBJECT(
        'theme',
        '플랫폼',
        'recommendations',
        JSON_ARRAY(
            JSON_OBJECT(
                'stock_code', '035420',
                'stock_name', 'NAVER',
                'recommendation', 'WATCH',
                'reason', '광고 성장 둔화와 커머스 경쟁 비용 증가를 확인할 필요가 있다.',
                'confidence', 0.7200
            ),
            JSON_OBJECT(
                'stock_code', '035720',
                'stock_name', '카카오',
                'recommendation', 'WATCH',
                'reason', '플랫폼 업종 전반의 광고 둔화 우려가 단기 부담이다.',
                'confidence', 0.6800
            )
        )
    ),
    '2026-05-11 12:00:00'
FROM users u
WHERE u.email = 'seungbin@example.com';

INSERT INTO stock_recommendations (analysis_id, stock_id, rank_no, recommendation, reason, confidence)
SELECT a.analysis_id, s.stock_id, 1, 'BUY', 'AI 서버 투자 확대로 메모리와 반도체 수요 증가가 기대된다.', 0.8700
FROM llm_analysis a
JOIN stocks s ON s.stock_code = '005930'
WHERE a.input_summary LIKE 'AI 반도체%';

INSERT INTO stock_recommendations (analysis_id, stock_id, rank_no, recommendation, reason, confidence)
SELECT a.analysis_id, s.stock_id, 2, 'BUY', 'HBM 수요 확대와 메모리 업황 회복 기대가 크다.', 0.8400
FROM llm_analysis a
JOIN stocks s ON s.stock_code = '000660'
WHERE a.input_summary LIKE 'AI 반도체%';

INSERT INTO stock_recommendations (analysis_id, stock_id, rank_no, recommendation, reason, confidence)
SELECT a.analysis_id, s.stock_id, 1, 'BUY', '전기차 수요 회복과 북미 생산 확대에 따른 성장 기대가 있다.', 0.8600
FROM llm_analysis a
JOIN stocks s ON s.stock_code = '373220'
WHERE a.input_summary LIKE '전기차%';

INSERT INTO stock_recommendations (analysis_id, stock_id, rank_no, recommendation, reason, confidence)
SELECT a.analysis_id, s.stock_id, 2, 'BUY', '고부가 배터리 중심의 수익성 개선 가능성이 있다.', 0.8000
FROM llm_analysis a
JOIN stocks s ON s.stock_code = '006400'
WHERE a.input_summary LIKE '전기차%';

INSERT INTO stock_recommendations (analysis_id, stock_id, rank_no, recommendation, reason, confidence)
SELECT a.analysis_id, s.stock_id, 3, 'WATCH', '소재 가격 안정은 긍정적이지만 업황 회복 확인이 더 필요하다.', 0.6900
FROM llm_analysis a
JOIN stocks s ON s.stock_code = '003670'
WHERE a.input_summary LIKE '전기차%';

INSERT INTO stock_recommendations (analysis_id, stock_id, rank_no, recommendation, reason, confidence)
SELECT a.analysis_id, s.stock_id, 1, 'WATCH', '광고 성장 둔화와 커머스 경쟁 비용 증가를 확인할 필요가 있다.', 0.7200
FROM llm_analysis a
JOIN stocks s ON s.stock_code = '035420'
WHERE a.input_summary LIKE '광고 시장%';

INSERT INTO stock_recommendations (analysis_id, stock_id, rank_no, recommendation, reason, confidence)
SELECT a.analysis_id, s.stock_id, 2, 'WATCH', '플랫폼 업종 전반의 광고 둔화 우려가 단기 부담이다.', 0.6800
FROM llm_analysis a
JOIN stocks s ON s.stock_code = '035720'
WHERE a.input_summary LIKE '광고 시장%';

INSERT INTO analysis_news_articles (analysis_id, article_id)
SELECT a.analysis_id, n.article_id
FROM llm_analysis a
JOIN news_articles n
WHERE a.input_summary LIKE 'AI 반도체%'
  AND n.url IN (
      'https://news.example.com/ai-semiconductor-demand',
      'https://news.example.com/hbm-supply-shortage',
      'https://news.example.com/semiconductor-export-recovery'
  );

INSERT INTO analysis_news_articles (analysis_id, article_id)
SELECT a.analysis_id, n.article_id
FROM llm_analysis a
JOIN news_articles n
WHERE a.input_summary LIKE '전기차%'
  AND n.url IN (
      'https://news.example.com/ev-sales-recovery',
      'https://news.example.com/battery-material-price',
      'https://news.example.com/north-america-battery-investment'
  );

INSERT INTO analysis_news_articles (analysis_id, article_id)
SELECT a.analysis_id, n.article_id
FROM llm_analysis a
JOIN news_articles n
WHERE a.input_summary LIKE '광고 시장%'
  AND n.url IN (
      'https://news.example.com/platform-ad-slowdown',
      'https://news.example.com/platform-commerce-competition'
  );
