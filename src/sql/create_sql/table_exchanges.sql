CREATE TABLE IF NOT EXISTS coingecko.exchanges (
    _ts timestamptz NOT NULL,
    id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL, 
    year_established INT, 
    country VARCHAR(255),
    description TEXT,
    url VARCHAR(355),
    image VARCHAR(355),
    has_trading_incentive Bool,
    trust_score Smallint,
    trust_score_rank Smallint,
    trade_volume_24h_btc Numeric,
    trade_volume_24h_btc_normalized Numeric,
    PRIMARY KEY (_ts, id)
);