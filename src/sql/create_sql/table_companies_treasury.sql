CREATE TABLE IF NOT EXISTS coingecko.companies_treasury (
    _ts timestamptz NOT NULL,
    coin_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL, 
    symbol VARCHAR NOT NULL,
    country VARCHAR,
    company_holdings BIGINT,
    company_entry_value_usd BIGINT,
    company_current_value_usd BIGINT,
    percentage_of_company_supply DECIMAL(7, 3),
    total_companies_holdings Numeric,
    total_companies_value_usd Numeric,
    total_companies_market_cap_dominance Numeric,
    PRIMARY KEY (_ts, coin_id, name)
);