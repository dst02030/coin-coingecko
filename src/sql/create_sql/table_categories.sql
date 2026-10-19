CREATE TABLE IF NOT EXISTS coingecko.categories (
    _ts timestamptz NOT NULL,
    id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL, 
    market_cap Numeric,
    market_cap_change_24h Numeric,
    content TEXT,
    top_3_coins_id Varchar[],
    top_3_coins Varchar[],
    volume_24h Numeric,
    updated_at timestamptz,
    PRIMARY KEY (_ts, id)
);