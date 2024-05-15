CREATE TABLE IF NOT EXISTS coingecko.global (
    _ts timestamptz NOT NULL,
    active_cryptocurrencies INT,
    ended_icos INT,
    market_cap_change_percentage_24h_usd DECIMAL(10, 6),
    market_cap_percentage JSON,
    markets INT,
    ongoing_icos INT,
    total_market_cap JSON,
    total_volume JSON,
    upcoming_icos INT,
    updated_at Numeric,
    PRIMARY KEY (_ts)
);