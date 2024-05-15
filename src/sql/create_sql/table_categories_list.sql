CREATE TABLE IF NOT EXISTS coingecko.categories_list (
    _ts timestamptz NOT NULL,
    category_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL, 
    PRIMARY KEY (category_id)
);