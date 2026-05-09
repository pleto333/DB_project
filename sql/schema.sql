CREATE DATABASE IF NOT EXISTS stock_prediction_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE stock_prediction_db;

DROP TABLE IF EXISTS stock_recommendations;
DROP TABLE IF EXISTS llm_analysis;
DROP TABLE IF EXISTS user_reports;
DROP TABLE IF EXISTS stock_predictions;
DROP TABLE IF EXISTS sentiment_analysis;
DROP TABLE IF EXISTS news_articles;
DROP TABLE IF EXISTS stock_prices;
DROP TABLE IF EXISTS user_holdings;
DROP TABLE IF EXISTS stocks;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_users_username UNIQUE (username),
    CONSTRAINT uk_users_email UNIQUE (email)
) ENGINE=InnoDB;

CREATE TABLE stocks (
    stock_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100) NOT NULL,
    market ENUM('KOSPI', 'KOSDAQ', 'NASDAQ', 'NYSE', 'OTHER') NOT NULL DEFAULT 'KOSPI',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_stocks_stock_code UNIQUE (stock_code),
    INDEX idx_stocks_stock_name (stock_name)
) ENGINE=InnoDB;

CREATE TABLE news_articles (
    article_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    summary TEXT NULL,
    url VARCHAR(1000) NOT NULL,
    url_hash CHAR(64) NOT NULL,
    publisher VARCHAR(100) NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'ls_securities',
    published_at DATETIME NULL,
    collected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_news_articles_url_hash UNIQUE (url_hash),
    INDEX idx_news_articles_published_at (published_at),
    INDEX idx_news_articles_collected_at (collected_at)
) ENGINE=InnoDB;

CREATE TABLE llm_analysis (
    analysis_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NULL,
    model_name VARCHAR(100) NOT NULL,
    input_summary TEXT NOT NULL,
    response_json JSON NOT NULL,
    analyzed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_llm_analysis_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    INDEX idx_llm_analysis_user_id (user_id),
    INDEX idx_llm_analysis_analyzed_at (analyzed_at)
) ENGINE=InnoDB;

CREATE TABLE stock_recommendations (
    recommendation_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    analysis_id BIGINT UNSIGNED NOT NULL,
    stock_id BIGINT UNSIGNED NOT NULL,
    rank_no INT UNSIGNED NOT NULL,
    recommendation ENUM('BUY', 'WATCH') NOT NULL DEFAULT 'WATCH',
    reason TEXT NOT NULL,
    confidence DECIMAL(5, 4) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_stock_recommendations_analysis_rank UNIQUE (analysis_id, rank_no),
    CONSTRAINT chk_stock_recommendations_confidence CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
    CONSTRAINT fk_stock_recommendations_analysis
        FOREIGN KEY (analysis_id) REFERENCES llm_analysis (analysis_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_stock_recommendations_stock
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    INDEX idx_stock_recommendations_analysis_id (analysis_id),
    INDEX idx_stock_recommendations_stock_id (stock_id)
) ENGINE=InnoDB;
