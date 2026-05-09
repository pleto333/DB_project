CREATE DATABASE IF NOT EXISTS stock_prediction_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE stock_prediction_db;

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NULL,
    phone_number VARCHAR(30) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_users_username UNIQUE (username),
    CONSTRAINT uk_users_email UNIQUE (email),
    INDEX idx_users_created_at (created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS stocks (
    stock_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100) NOT NULL,
    market ENUM('KOSPI', 'KOSDAQ', 'NASDAQ', 'NYSE', 'AMEX', 'ETF', 'OTHER') NOT NULL DEFAULT 'OTHER',
    currency CHAR(3) NOT NULL DEFAULT 'KRW',
    sector VARCHAR(100) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_stocks_stock_code UNIQUE (stock_code),
    INDEX idx_stocks_stock_name (stock_name),
    INDEX idx_stocks_market (market)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_holdings (
    holding_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    stock_id BIGINT UNSIGNED NOT NULL,
    quantity DECIMAL(18, 4) NOT NULL,
    average_buy_price DECIMAL(18, 4) NOT NULL,
    buy_date DATE NOT NULL,
    memo VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_user_holdings_user_stock UNIQUE (user_id, stock_id),
    CONSTRAINT chk_user_holdings_quantity CHECK (quantity > 0),
    CONSTRAINT chk_user_holdings_average_buy_price CHECK (average_buy_price > 0),
    CONSTRAINT fk_user_holdings_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_user_holdings_stock
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    INDEX idx_user_holdings_user_id (user_id),
    INDEX idx_user_holdings_stock_id (stock_id),
    INDEX idx_user_holdings_buy_date (buy_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS stock_prices (
    price_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    stock_id BIGINT UNSIGNED NOT NULL,
    current_price DECIMAL(18, 4) NOT NULL,
    open_price DECIMAL(18, 4) NULL,
    high_price DECIMAL(18, 4) NULL,
    low_price DECIMAL(18, 4) NULL,
    close_price DECIMAL(18, 4) NULL,
    trading_volume BIGINT UNSIGNED NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'manual',
    collected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_stock_prices_current_price CHECK (current_price >= 0),
    CONSTRAINT chk_stock_prices_open_price CHECK (open_price IS NULL OR open_price >= 0),
    CONSTRAINT chk_stock_prices_high_price CHECK (high_price IS NULL OR high_price >= 0),
    CONSTRAINT chk_stock_prices_low_price CHECK (low_price IS NULL OR low_price >= 0),
    CONSTRAINT chk_stock_prices_close_price CHECK (close_price IS NULL OR close_price >= 0),
    CONSTRAINT uk_stock_prices_stock_time_source UNIQUE (stock_id, collected_at, source),
    CONSTRAINT fk_stock_prices_stock
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    INDEX idx_stock_prices_stock_id (stock_id),
    INDEX idx_stock_prices_collected_at (collected_at),
    INDEX idx_stock_prices_stock_collected_at (stock_id, collected_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS news_articles (
    article_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    stock_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(300) NOT NULL,
    summary TEXT NULL,
    url VARCHAR(1000) NOT NULL,
    url_hash CHAR(64) NOT NULL,
    publisher VARCHAR(100) NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'google_news_rss',
    language CHAR(2) NOT NULL DEFAULT 'ko',
    published_at DATETIME NULL,
    collected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_news_articles_url_hash UNIQUE (url_hash),
    CONSTRAINT fk_news_articles_stock
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    INDEX idx_news_articles_stock_id (stock_id),
    INDEX idx_news_articles_published_at (published_at),
    INDEX idx_news_articles_collected_at (collected_at),
    INDEX idx_news_articles_stock_published_at (stock_id, published_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sentiment_analysis (
    sentiment_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    article_id BIGINT UNSIGNED NOT NULL,
    sentiment_label ENUM('Positive', 'Neutral', 'Negative') NOT NULL,
    sentiment_score TINYINT NOT NULL,
    confidence DECIMAL(5, 4) NULL,
    analyzed_model VARCHAR(100) NOT NULL DEFAULT 'rule_based_v1',
    analyzed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_sentiment_analysis_article UNIQUE (article_id),
    CONSTRAINT chk_sentiment_analysis_score CHECK (sentiment_score IN (-1, 0, 1)),
    CONSTRAINT chk_sentiment_analysis_confidence CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
    CONSTRAINT fk_sentiment_analysis_article
        FOREIGN KEY (article_id) REFERENCES news_articles (article_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    INDEX idx_sentiment_analysis_article_id (article_id),
    INDEX idx_sentiment_analysis_score (sentiment_score),
    INDEX idx_sentiment_analysis_analyzed_at (analyzed_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS stock_predictions (
    prediction_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    stock_id BIGINT UNSIGNED NOT NULL,
    prediction_date DATE NOT NULL,
    prediction_direction ENUM('UP', 'DOWN', 'NEUTRAL') NOT NULL DEFAULT 'NEUTRAL',
    predicted_change_rate DECIMAL(9, 4) NULL,
    predicted_price DECIMAL(18, 4) NULL,
    sentiment_avg_score DECIMAL(6, 4) NULL,
    confidence DECIMAL(5, 4) NULL,
    basis_start_at DATETIME NULL,
    basis_end_at DATETIME NULL,
    model_name VARCHAR(100) NOT NULL DEFAULT 'sentiment_average_model',
    model_version VARCHAR(30) NOT NULL DEFAULT 'v1',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_stock_predictions_stock_date_model UNIQUE (stock_id, prediction_date, model_name, model_version),
    CONSTRAINT chk_stock_predictions_confidence CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
    CONSTRAINT fk_stock_predictions_stock
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    INDEX idx_stock_predictions_stock_id (stock_id),
    INDEX idx_stock_predictions_prediction_date (prediction_date),
    INDEX idx_stock_predictions_stock_date (stock_id, prediction_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_reports (
    report_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    stock_id BIGINT UNSIGNED NOT NULL,
    prediction_id BIGINT UNSIGNED NULL,
    report_title VARCHAR(200) NOT NULL,
    report_content TEXT NOT NULL,
    profit_rate DECIMAL(9, 4) NULL,
    profit_amount DECIMAL(20, 4) NULL,
    recommendation ENUM('BUY', 'HOLD', 'SELL', 'WATCH') NOT NULL DEFAULT 'HOLD',
    generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_user_reports_user_stock_generated UNIQUE (user_id, stock_id, generated_at),
    CONSTRAINT fk_user_reports_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_user_reports_stock
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_user_reports_prediction
        FOREIGN KEY (prediction_id) REFERENCES stock_predictions (prediction_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    INDEX idx_user_reports_user_id (user_id),
    INDEX idx_user_reports_stock_id (stock_id),
    INDEX idx_user_reports_generated_at (generated_at),
    INDEX idx_user_reports_user_generated_at (user_id, generated_at)
) ENGINE=InnoDB;
