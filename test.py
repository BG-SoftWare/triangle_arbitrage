from binance.websocket.spot.websocket_client import SpotWebsocketClient as WebsocketClient
from binance.spot import Spot as Client
import time
import os
import json
import certifi
import config


ASK_PRICE = 0
BID_PRICE = 0


os.environ['SSL_CERT_FILE'] = certifi.where()
spot_client = Client(base_url="https://api.binance.com")

with open("arbitrage_opportunity.json", "r") as arb_file:
    arbitrage_opportunities = json.load(arb_file)


def runtime(some_function):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = some_function(*args, **kwargs)
        print(time.time() - start_time)
        return result

    return wrapper


@runtime
def get_triangle_combinations(base):
    combinations = []
    with open("trading_tickers.json", "r") as symbols_file:
        tickers = json.load(symbols_file)
    with open("data.json", "r") as data_file:
        data = json.load(data_file)
    for sym1 in data:
        sym1_token1 = sym1[0]
        sym1_token2 = sym1[1]
        if sym1_token2 == base:
            for sym2 in data:
                sym2_token1 = sym2[0]
                sym2_token2 = sym2[1]
                if sym1_token1 == sym2_token2:
                    for sym3 in data:
                        sym3_token1 = sym3[0]
                        sym3_token2 = sym3[1]
                        if (sym2_token1 == sym3_token1) and (sym3_token2 == sym1_token2):
                            combination = {
                                'first': f'{sym1_token2}{sym1_token1}'
                                if f'{sym1_token2}{sym1_token1}' in tickers else f'{sym1_token1}{sym1_token2}',
                                'second': f'{sym1_token1}{sym2_token1}'
                                if f'{sym1_token1}{sym2_token1}' in tickers else f'{sym2_token1}{sym1_token1}',
                                'third': f'{sym2_token1}{sym1_token2}'
                                if f'{sym2_token1}{sym1_token2}' in tickers else f'{sym1_token2}{sym2_token1}'
                            }
                            combinations.append(combination)
    print(len(combinations))
    with open("arbitrage_opportunity.json", "w") as triang_file:
        json.dump(combinations, triang_file)


def update_trading_pairs():
    result_data = []
    exc_data = spot_client.exchange_info()["symbols"]
    for ticker in exc_data:
        if ticker["status"] != "BREAK":
            result_data.append([ticker["baseAsset"], ticker["quoteAsset"]])
    with open("data.json", "w") as data_file:
        json.dump(result_data, data_file)


ws_client = WebsocketClient()
ws_client.start()


def handler(message):
    try:
        config.tickers_prices[message['s']] = {"ask_price": message['a'], "bid_price": message['b']}
    except Exception:
        pass


ws_client.book_ticker(
        id=1,
        callback=handler
    )


def get_prices_and_calculate_profit():
    for bundle in arbitrage_opportunities:
        route = get_route(bundle)
        print(f"Проверка связки {bundle}")
        if route[0] == "sell":
            first_price = config.tickers_prices[bundle['first']]['bid_price']
            second_qty = config.base_qty * first_price * config.fee_percentage
            print(f"Продаем {second_qty} {bundle['first']} по цене {first_price}")
        elif route[0] == "buy":
            first_price = config.tickers_prices[bundle['first']]['ask_price']
            second_qty = config.base_qty / first_price * config.fee_percentage
            print(f"Покупаем {second_qty} {bundle['first']} по цене {first_price}")
        else:
            print("Invalid data (first ticker)")

        if route[1] == "sell":
            second_price = config.tickers_prices[bundle['second']]['bid_price']
            third_qty = second_qty * second_price * config.fee_percentage
            print(f"Продаем {third_qty} {bundle['second']} по цене {second_price}")
        elif route[1] == "buy":
            second_price = config.tickers_prices[bundle['second']]['ask_price']
            third_qty = second_qty / second_price * config.fee_percentage
            print(f"Покупаем {third_qty} {bundle['second']} по цене {second_price}")
        else:
            print("Invalid data (second ticker)")

        if route[2] == "sell":
            third_price = config.tickers_prices[bundle['third']]['bid_price']
            result_qty = third_qty * third_price * config.fee_percentage
            print(f"Продаем {result_qty} {bundle['third']} по цене {third_price}")
        elif route[2] == "buy":
            third_price = config.tickers_prices[bundle['third']]['ask_price']
            result_qty = third_qty / third_price * config.fee_percentage
            print(f"Покупаем {result_qty} {bundle['third']} по цене {third_price}")
        else:
            print("Invalid data (third ticker)")
        profit = result_qty - config.base_qty
        if profit > config.profit:
            print(f"WE HAVE ARBITRAGE OPPORTUNITY. OUR PROFIT IS {profit} {config.base}")


def get_route(bundle):
    if bundle['first'].startswith(config.base):
        first_side = "sell"
        second_token = bundle['first'][len(config.base):]
    elif bundle['first'].endswith(config.base):
        first_side = "buy"
        second_token = bundle['first'][:-len(config.base)]
    if bundle['second'].startswith(second_token):
        second_side = "sell"
        third_token = bundle['second'][len(second_token):]
    elif bundle['second'].endswith(second_token):
        second_side = "buy"
        third_token = bundle['second'][:-len(second_token)]
    if bundle['third'].startswith(third_token):
        third_side = "sell",
    elif bundle['third'].endswith(third_token):
        third_side = "buy"
    return first_side, second_side, third_side
get_prices_and_calculate_profit()

# while 1:
#     try:
#         get_prices_and_calculate_profit()
#     except Exception:
#         pass


# def get_prices(base):
#     bnb_price = spot_client.ticker_price(symbol="BNB")
#     for pair in arbitrage_opportunity:
#         first_price = spot_client.ticker_price(pair['first'])
#         second_price = spot_client.ticker_price(pair['first'])
#         third_price = spot_client.ticker_price(pair['first'])



# first_price = ws_client.partial_book_depth(
#     id=1,
#     level=5,
#     speed=100,
#     symbol="btcusdt"
# )


# price = ws_client.partial_book_depth(
#     symbol="BTCUSDT",
#     id=1,
#     level=5,
#     speed=100,
#     callback=handler
# )

# @runtime
# def get_tickers_price():
#     for bundle in arbitrage_opportunity:
#         price = spot_client.ticker_price(
#             symbols=[bundle["first"], bundle["second"], bundle["third"]]
#         )
#         print(price)


# get_tickers_price()
# for bundle in arbitrage_bundles:
#     first_price = ws_client.book_ticker(
#         id=1,
#         symbol=bundle["first"],
#         callback=price_extractor
#     )
#     second_price = ws_client.book_ticker(
#         id=2,
#         symbol=bundle["second"],
#         callback=price_extractor
#     )
#     third_price = ws_client.book_ticker(
#         id=3,
#         symbol=bundle["third"],
#         callback=price_extractor
#     )
#     print(first_price, second_price, third_price)


# busd_combinations = get_triangle_combinations('BUSD')






# base = "PORTO"
#
# data_1 = [{"PORTO": "TRY"}, ]
# data_2 = { "TRY": "EUR"}
# data_3 = { "EUR": "PORTO"}
#
# data_2_base_keys = [item[1] for item in data_1]
