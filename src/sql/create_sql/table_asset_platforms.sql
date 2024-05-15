CREATE TABLE IF NOT EXISTS coingecko.asset_platforms (
    _ts timestamptz NOT NULL,
    id VARCHAR(255),
    chain_identifier NUMERIC,
    name VARCHAR(255) NOT NULL, 
    shortname VARCHAR(255),
    native_coin_id VARCHAR(255),
    PRIMARY KEY (name)
);