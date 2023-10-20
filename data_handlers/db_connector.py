from sqlalchemy import Table, Column, Integer, String, MetaData, Text, DateTime
from sqlalchemy import create_engine, select, insert, and_
from sqlalchemy import DECIMAL
import datetime

with open(".env", "r") as env_file:
    keys = env_file.readlines()

DB_USERNAME = keys[2].split("=")[1].rstrip()
DB_PASSWORD = keys[3].split("=")[1].rstrip()
DB_HOST = keys[4].split("=")[1].rstrip()


class DatabaseConnector(object):
    meta = MetaData()

    triangle_arbitrage = Table(
        "triangle_arbitrage", meta,
        Column('id', Integer, primary_key=True),
        Column('combinations', String(255)),
        Column('fee_amount', String(255)),
        Column('profit_amount', DECIMAL(26, 16)),
        Column('profit_percentage', DECIMAL(26, 16)),
        Column('best_depth_prices', Text),
        Column('best_depth_qty', Text),
        Column('checking_time', DateTime, default=datetime.datetime.now)
    )

    trading = Table(
        "trading", meta,
        Column('id', Integer, primary_key=True),
        Column('symbol', String(255)),
        Column('order_id', String(255)),
        Column('order_status', String(255)),
        Column('quantity', String(255)),
        Column('price', String(255)),
        Column('fee_asset', String(255)),
        Column('fee_amount', String(255)),
        Column('quote_order_qty', String(255)),
        Column('transaction_time', String(255)),
        Column('inserting_time', DateTime, default=datetime.datetime.now)
    )

    new_order_response = Table(
        "new_order_response", meta,
        Column('id', Integer, primary_key=True),
        Column('symbol', String(255)),
        Column('order_id', String(255)),
        Column('order_status', String(255)),
        Column('quantity', String(255)),
        Column('price', String(255)),
        Column('fee_asset', String(255)),
        Column('fee_amount', String(255)),
        Column('quote_order_qty', String(255)),
        Column('transaction_time', String(255)),
        Column('inserting_time', DateTime, default=datetime.datetime.now)
    )

    balance_exchanges = Table(
        "balance_exchanges", meta,
        Column('id', Integer, primary_key=True),
        Column('order_id', String(255)),
        Column('base_asset', String(255)),
        Column('base_balance', DECIMAL(26, 16)),
        Column('quote_asset', String(255)),
        Column('quote_balance', DECIMAL(26, 16))
    )

    wallet_update = Table(
        "wallet_update", meta,
        Column('id', Integer, primary_key=True),
        Column('asset', String(255)),
        Column('balance_delta', DECIMAL(26, 16)),
        Column('update_time', String(255))
    )

    depth = Table(
        "depth", meta,
        Column('id', Integer, primary_key=True),
        Column('ticker', String(20)),
        Column('bids', Text),
        Column('asks', Text),
        Column('Time', DateTime, default=datetime.datetime.now)
    )

    prices = Table(
        "prices", meta,
        Column('pair', String(50)),
        Column('bid_price', String(255)),
        Column('ask_price', String(255)),
        Column('last_update', DateTime, default=datetime.datetime.now)
    )

    table_names = {
        "triangle_arbitrage": triangle_arbitrage,
        "trading": trading,
        "balance_exchanges": balance_exchanges,
        "wallet_update": wallet_update,
        "depth": depth,
        "new_order_response": new_order_response,
        "prices": prices
    }

    def __init__(self, logger):
        self.logger = logger
        self.engine = create_engine(f'mysql+mysqlconnector://{DB_USERNAME}:'
                                    f'{DB_PASSWORD}@{DB_HOST}/arbitrage', pool_pre_ping=True)
        self.meta.bind = self.engine
        self.meta.create_all()

    def insert_data(self, insert_queue):
        while not insert_queue.empty():
            data_for_insert = insert_queue.get()
            table_name = data_for_insert["table_name"]
            data = data_for_insert["data"]

            conn = self.engine.connect().execution_options(autocommit=True)
            self.logger.info(f"Insert data to table {table_name}")
            try:
                conn.execute(insert(self.table_names[table_name]), data)
                self.logger.info(f"Insert to {table_name} was SUCCESSFUL")
            except KeyError:
                self.logger.error(f"Unknown table name {table_name}. Insert status FAILED")
            except Exception as other_error:
                self.logger.critical(f"Insert to {table_name} was FAILED")
                self.logger.error(other_error)

            conn.close()
            self.engine.dispose()

    def select_price(self, pairs):
        conn = self.engine.connect()
        data = conn.execute(
            select([
                self.prices.c.pair,
                self.prices.c.bid_price,
                self.prices.c.ask_price
            ]).where(and_(
                self.prices.c.pair == pairs[0],
                self.prices.c.pair == pairs[1],
                self.prices.c.pair == pairs[2]
            ))
        )
        result = data.fetchall()
        return result

    def select_data(self):
        conn = self.engine.connect()
        data = conn.execute(
            select(
                [
                    self.triangle_arbitrage.c.id,
                    self.triangle_arbitrage.c.combinations,
                    self.triangle_arbitrage.c.fee_amount,
                    self.triangle_arbitrage.c.is_arbitrage_opportunity,
                    self.triangle_arbitrage.c.profit_amount,
                    self.triangle_arbitrage.c.profit_percentage,
                    self.triangle_arbitrage.c.best_depth_prices,
                    self.triangle_arbitrage.c.best_depth_qty,
                    self.triangle_arbitrage.c.cchecking_time
                ]
            )
        )
        result = data.fetchall()
        conn.close()
        self.engine.dispose()
        return result
