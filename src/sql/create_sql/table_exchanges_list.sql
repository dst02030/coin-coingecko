CREATE TABLE IF NOT EXISTS coingecko.exchanges_list (
    _ts timestamptz NOT NULL,
    id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL, 
    PRIMARY KEY (id)
);