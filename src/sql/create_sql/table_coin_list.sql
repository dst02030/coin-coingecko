CREATE TABLE IF NOT EXISTS coingecko.coin_list (
    _ts timestamptz NOT NULL,
    id VARCHAR(255) NOT NULL,
    symbol VARCHAR(255) NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    platforms JSON,
    PRIMARY KEY (id)
);