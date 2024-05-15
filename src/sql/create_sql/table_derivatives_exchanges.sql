CREATE TABLE IF NOT EXISTS coingecko.derivatives_exchanges (
    _ts timestamptz NOT NULL,
    name VARCHAR(255) NOT NULL,
    id VARCHAR(255) NOT NULL, 
    open_interest_btc Numeric,
    trade_volume_24h_btc Numeric,
    number_of_perpetual_pairs INT,
    number_of_futures_pairs INT,
    image VARCHAR NOT NULL,
    year_established INT,
    country VARCHAR,
    description VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    PRIMARY KEY (_ts, name)
);