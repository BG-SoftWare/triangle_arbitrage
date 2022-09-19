from binance.websocket.spot.websocket_client import SpotWebsocketClient as WebsocketClient
from binance.spot import Spot as Client
import time
import os
import json
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
spot_client = Client(base_url="https://api.binance.com")


with open("arbitrage_opportunity.json", "r") as arb_file:
    arbitrage_opportunity = json.load(arb_file)


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


# def handler(data):
#     print(data)
#
#
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
