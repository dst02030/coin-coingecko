CREATE TABLE IF NOT EXISTS coingecko.derivatives (
    _ts timestamptz NOT NULL,
    market VARCHAR(255) NOT NULL,
    symbol VARCHAR(255) NOT NULL, 
    index_id VARCHAR NOT NULL, 
    price Numeric,
    price_percentage_change_24h Numeric NOT NULL,
    contract_type VARCHAR NOT NULL,
    index Numeric,
    basis Numeric NOT NULL,
    spread Numeric,
    funding_rate Numeric NOT NULL,
    open_interest Numeric,
    volume_24h Numeric NOT NULL,
    last_traded_at BIGINT NOT NULL,
    expired_at BIGINT,
    PRIMARY KEY (_ts, market, symbol, index_id)
);