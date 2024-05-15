CREATE TABLE IF NOT EXISTS coingecko.nfts_list (
    _ts timestamptz NOT NULL,
    id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    contract_address VARCHAR, 
    asset_platform_id VARCHAR, 
    symbol VARCHAR,
    PRIMARY KEY (id)
);