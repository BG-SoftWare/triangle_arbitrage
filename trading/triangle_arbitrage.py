import json
import os
import sys
import time
from ast import literal_eval
from decimal import Decimal, ROUND_FLOOR

import certifi
from binance.spot import Spot as Client
from redis import Redis

import config
import logger
from trading_bot import TradingBot

os.environ['SSL_CERT_FILE'] = certifi.where()

with open(".env", "r") as file:
    keys = file.readlines()

api_key = keys[0].split("=")[1].rstrip()
secret_key = keys[1].split("=")[1].rstrip()

host_name = keys[5].split("=")[1].rstrip()
port = keys[6].split("=")[1].rstrip()
password = keys[7].split("=")[1].rstrip()

fields_by_side = {
    "SELL": {
        "qty_after_trade": "cummulativeQuoteQty",
        "qty_for_trade": "origQty",
        "reverse_side": "BUY",
    },
    "BUY": {
        "qty_after_trade": "origQty",
        "qty_for_trade": "cummulativeQuoteQty",
        "reverse_side": "SELL",
    }
}


class TriangleArbitrage:
    def __init__(self):
        self.base_token = config.base_token
        self.bot = TradingBot()
        self.logger = logger.get_logger("PROFIT CALCULATOR")
        self.spot_client = Client(api_key, secret_key, base_url="https://api.binance.com")
        self.trading_pairs = dict()
        self.current_ticker_qty = 0.0
        self.pairs_list = []
        self.redis_client = Redis(host=host_name, port=port, password=password, db=0)
        self.unprofitable_counter = 0
        self.file_reader()

    def file_reader(self):
        with open(f"source/arbitrage_combinations_{self.base_token.lower()}.json", "r") as combination_file:
            self.pairs_list = json.load(combination_file)

        with open("../source/trading_pairs.json", "r") as trade_file:
            self.trading_pairs = json.load(trade_file)

    def get_prices(self, combination):
        prices = []
        try:
            deserialize_prices = self.redis_client.mget(combination)
        except Exception:
            self.logger.warning("The Redis returned an error.", exc_info=True)
            return None

        try:
            for index, price in enumerate(deserialize_prices):
                if price is not None:
                    prices.append(json.loads(price.decode("utf-8")))
                else:
                    spot_price = self.spot_client.depth(list(combination.values())[index])
                    prices.append(spot_price)
                    self.redis_client.set(list(combination.values())[index],
                                          json.dumps({
                                              'bid_price': json.dumps(spot_price["bids"]),
                                              'ask_price': json.dumps(spot_price["asks"])
                                          })
                                          )
            return prices
        except Exception:
            self.logger.warning("Price handling was FAILED", exc_info=True)
            return None

    def calculate_profit(self):
        for combinations in self.pairs_list:
            ticker_prices = []
            ticker_quantities = []
            fee_amount = []
            start_and_end_qty_base_token = []

            combination = combinations["combination"]
            routes = combinations["routes"]
            current_ticker_qty = Decimal(config.start_qty)
            prices = self.get_prices(combination.values())
            if prices is None:
                continue
            for index, ticker in enumerate(list(combination.values())):
                if routes[index].lower() == "sell":
                    pair_price_for_calculate = Decimal(literal_eval(prices[index]["bid_price"])[0][0])
                    qty_for_order = self.__qty_filter(ticker, current_ticker_qty)
                    ticker_qty_after_trade = Decimal(qty_for_order * pair_price_for_calculate)
                    if index == 0:
                        start_and_end_qty_base_token.append(qty_for_order)
                    elif index == 2:
                        start_and_end_qty_base_token.append(ticker_qty_after_trade)
                    ticker_quantities.append(qty_for_order)
                    current_ticker_qty = ticker_qty_after_trade
                    pair_price_for_order = Decimal(literal_eval(prices[index]["bid_price"])[0][0])

                else:
                    pair_price_for_calculate = Decimal(literal_eval(prices[index]["ask_price"])[0][0])
                    qty_for_order = Decimal(current_ticker_qty / pair_price_for_calculate)
                    filtered_qty_for_order = self.__qty_filter(ticker, qty_for_order)
                    amount_of_token_spent = filtered_qty_for_order * pair_price_for_calculate
                    if index == 0:
                        start_and_end_qty_base_token.append(amount_of_token_spent)
                    elif index == 2:
                        start_and_end_qty_base_token.append(filtered_qty_for_order)
                    ticker_quantities.append(filtered_qty_for_order)
                    current_ticker_qty = filtered_qty_for_order
                    pair_price_for_order = Decimal(literal_eval(prices[index]["ask_price"])[0][0])

                fee = current_ticker_qty * Decimal(config.fee_percentage) / 100
                fee_amount.append(fee)
                ticker_prices.append(pair_price_for_order)

            if len(ticker_quantities) == 3:
                profit_delta = start_and_end_qty_base_token[-1] - start_and_end_qty_base_token[0]
                sum_fee_amount = Decimal(fee_amount[-1]) * 3
                profit = profit_delta - sum_fee_amount
                profit_percentage = profit_delta / start_and_end_qty_base_token[0] * 100
                if profit >= Decimal(config.profit):
                    self.logger.info(f"There is an arbitration window for {combination}."
                                     f"Profit: {profit} {self.base_token}")

                    deserialize_data_before_trade = self.redis_client.mget(combination.values())
                    serialize_data_before_trade = [json.loads(data.decode("utf-8"))
                                                   for data in deserialize_data_before_trade]

                    real_data = self.trading(combination, ticker_quantities, ticker_prices, routes)
                    self.order_handler(real_data)

                    deserialize_data_after_trade = self.redis_client.mget(combination.values())
                    serialize_data_after_trade = [json.loads(data.decode("utf-8"))
                                                  for data in deserialize_data_after_trade]

                    self.depth_insert(combination, serialize_data_before_trade, "before")
                    self.depth_insert(combination, serialize_data_after_trade, "after")

                    self.insert_calculated_data(combination, sum_fee_amount, profit, profit_percentage, prices)
            else:
                self.logger.warning(f"{combination} | Filter is FAILED. Something wrong.")

    def trading(self, combination: dict, quantities: list, prices: list, routes: list):
        self.bot.combination = combination
        orders_info = {}
        orders_responses = []
        self.bot.trade_flag = 0
        quantity_after_order = 0
        for index, pair in enumerate(combination.values()):
            self.logger.info(f"Trying create {index + 1} order.")
            if index == 0:
                quantity = quantities[0]
            else:
                if routes[index].lower() == "buy":
                    non_filtered_quantity = Decimal(quantity_after_order / Decimal(prices[index]))
                elif routes[index].lower() == "sell":
                    non_filtered_quantity = quantity_after_order
                quantity = self.__qty_filter(pair, non_filtered_quantity)

            order = self.bot.create_limit_order(
                ticker=pair,
                side=routes[index],
                price=prices[index],
                quantity=quantity
            )

            while not self.bot.trade_flag:
                if self.bot.need_rollback:
                    try:
                        rollback_order = self.rollback(combination, pair, quantity, routes)
                        if rollback_order == "FILLED":
                            self.bot.trade_flag = True
                        self.logger.info(f"The rollback from {index + 1} order was SUCCESSFUL.")
                        self.bot.need_rollback = False
                        orders_info["rollback"] = rollback_order
                        return orders_info
                    except Exception as exception:
                        if "Unknown order sent" in exception:
                            self.bot.trade_flag = True
                            continue
                        else:
                            rollback_order = False
                            self.logger.info(f"The rollback from {index + 1} order was FAILED.", exc_info=True)
                            return rollback_order
                time.sleep(1 / 1000)

            quantity_after_order = Decimal(order[fields_by_side[order['side']]['qty_after_trade']])
            orders_responses.append(order)
        orders_info["orders"] = orders_responses
        return orders_info

    def order_handler(self, orders_info):
        orders = orders_info.get("orders", None)
        rollback = orders_info.get("rollback", False)
        if not rollback:
            self.logger.info("Trades were successful")

            fee = 0
            start_qty = Decimal(orders[0][fields_by_side[orders[0]['side']]['qty_for_trade']])
            final_qty = Decimal(orders[-1][fields_by_side[orders[-1]['side']]['qty_after_trade']])

            for order in orders:
                fee += Decimal(sum([Decimal(com["commission"]) for com in order["fills"]]))

            real_delta = final_qty - start_qty
            real_profit = real_delta - (fee * Decimal(config.bnb_price_when_buy))

            if real_profit < 0:
                self.unprofitable_counter += 1
                if self.unprofitable_counter >= 3:
                    self.logger.warning("The last 3 trades were unprofitable. I stopped")
                    sys.exit()
            else:
                self.unprofitable_counter = 0
        else:
            self.logger.info("There was a rollback during trading.")
            if orders is not None:
                start_qty = Decimal(orders[0][fields_by_side[orders[0]['side']]['qty_for_trade']])
                rollback_ticker = rollback["symbol"]
                rollback_side = rollback["side"]
                rollback_fee = Decimal(sum([Decimal(com["commission"]) for com in rollback["fills"]]))
                qty_after_rollback = Decimal(rollback[fields_by_side[rollback_side]["qty_after_trade"]])
                self.logger.info(f"Rollback by ticker {rollback_ticker}. Real profit is:\n"
                                 f"{qty_after_rollback - start_qty - rollback_fee * Decimal(config.bnb_price_when_buy)}")

    def rollback(self, combination, ticker, qty, routes):
        if self.bot.order_status == "FILLED":
            return "FILLED"
        cancel_response = self.bot.cancel_order(
            ticker=ticker,
            order_id=self.bot.order_id
        )
        if cancel_response["status"] == "CANCELED":
            self.logger.info(f"Cancel order {ticker}")
            self.logger.info(cancel_response)
            try:
                if ticker == combination["first"]:
                    rollback_order = "The first order order in combination has been canceled."
                elif ticker == combination["second"]:
                    self.logger.info("The second order in combination has been canceled. Creating a rollback order")
                    if routes[0] == "buy":
                        rollback_order = self.spot_client.new_order(
                            symbol=combination["first"],
                            side="SELL",
                            type="MARKET",
                            quantity=qty
                        )
                    elif routes[0] == "sell":
                        rollback_order = self.spot_client.new_order(
                            symbol=combination["first"],
                            side="BUY",
                            type="MARKET",
                            quoteOrderQty=qty
                        )
                elif ticker == combination["third"]:
                    self.logger.info("The third order in combination has been canceled. Creating a rollback order")
                    if routes[2] == "sell":
                        rollback_order = self.spot_client.new_order(
                            symbol=combination["third"],
                            side="SELL",
                            type="MARKET",
                            quantity=qty
                        )
                    elif routes[2] == "buy":
                        rollback_order = self.spot_client.new_order(
                            symbol=combination["third"],
                            side="BUY",
                            type="MARKET",
                            quoteOrderQty=qty
                        )
                else:
                    rollback_order = None
                return rollback_order
            except Exception as e:
                self.logger.error("Rollback order not issued. ", e)
        else:
            self.logger.info("Can't cancel order.\n", cancel_response)

    def depth_insert(self, combination, data, before_or_after):
        for index, value in enumerate(combination.values()):
            data_for_insert = {
                "ticker": f"{value}_{before_or_after}",
                "bids": data[index]["bid_price"],
                "asks": data[index]["ask_price"]
            }
            self.bot.insert_queue.put({"table_name": "depth", "data": data_for_insert})

    def __qty_filter(self, ticker, qty):
        qty = Decimal(qty)
        lot_size_filter = self.trading_pairs[ticker]['lot_size']
        if Decimal(lot_size_filter['minQty']) <= Decimal(qty):
            filtered_qty = qty.quantize(Decimal(lot_size_filter['stepSize'].rstrip("0")), ROUND_FLOOR)
        else:
            filtered_qty = None
        return filtered_qty

    def insert_calculated_data(self, combination, fee_amount, profit, profit_percentage, prices):
        best_depth_prices = [
            {
                "bids": f"[{prices[0]['bid_price'][0][0]},"
                        f"{prices[1]['bid_price'][0][0]},"
                        f"{prices[2]['bid_price'][0][0]}]",
                "asks": f"[{prices[0]['ask_price'][0][0]},"
                        f"{prices[1]['ask_price'][0][0]},"
                        f"{prices[2]['ask_price'][0][0]}]"
            }
        ]

        data_for_insert_into_db = {
            'combinations': str(combination),
            'fee_amount': f'[{fee_amount}]',
            'profit_amount': profit,
            'profit_percentage': profit_percentage,
            'best_depth_prices': str(best_depth_prices),
            'best_depth_qty': json.dumps(prices),
        }
        data = {"table_name": "triangle_arbitrage", "data": data_for_insert_into_db}
        self.bot.insert_queue.put(data)

    def start(self):
        if Decimal(self.bot.base_balance) > (Decimal(config.start_qty) / 2):
            while not self.bot.start:
                time.sleep(1 / 1000)
            self.calculate_profit()

        else:
            self.logger.critical("We lost half of our working capital!!!!")
            sys.exit()
