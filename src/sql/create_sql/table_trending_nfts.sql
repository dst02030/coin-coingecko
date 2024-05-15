CREATE TABLE IF NOT EXISTS coingecko.trending_nfts (
    _ts timestamptz NOT NULL,
    id VARCHAR(255) NOT NULL,
    name VARCHAR NOT NULL, 
    symbol VARCHAR NOT NULL,
    thumb VARCHAR NOT NULL,
    nft_contract_id INT NOT NULL,
    native_currency_symbol VARCHAR NOT NULL,
    floor_price_in_native_currency NUMERIC NOT NULL,
    floor_price_24h_percentage_change Numeric NOT NULL,
    floor_price VARCHAR NOT NULL,
    floor_price_in_usd_24h_percentage_change Numeric NOT NULL,
    h24_volume VARCHAR NOT NULL,
    h24_average_sale_price VARCHAR NOT NULL,
    sparkline VARCHAR NOT NULL,
    content JSON,
    PRIMARY KEY (_ts, id)
);