CREATE TABLE IF NOT EXISTS coingecko.derivatives_exchanges_list (
    _ts timestamptz NOT NULL,
    id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    PRIMARY KEY (_ts, id)
);