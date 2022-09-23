create table triangle_arbitrage(
    id integer primary key,
    bunch varchar(255),
    fee_amount real,
    is_arbitrage_opportunity integer,
    profit_amount real,
    profit_percentage real,
    best_depth_prices varchar(255),
    best_depth_qty varchar(255),
    checking_time timestamp
);