CREATE TABLE IF NOT EXISTS coingecko.trending_categories (
    _ts timestamptz NOT NULL,
    id VARCHAR(255) NOT NULL,
    name VARCHAR NOT NULL, 
    market_cap_1h_change NUMERIC NOT NULL,
    slug VARCHAR NOT NULL,
    coins_count INT NOT NULL,
    market_cap NUMERIC NOT NULL,
    market_cap_btc NUMERIC NOT NULL,
    total_volume Numeric NOT NULL,
    total_volume_btc VARCHAR NOT NULL,
    market_cap_change_percentage_24h JSON NOT NULL,
    sparkline VARCHAR NOT NULL,
    PRIMARY KEY (_ts, id)
);