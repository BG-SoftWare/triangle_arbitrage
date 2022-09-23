from binance.websocket.spot.websocket_client import SpotWebsocketClient as WebsocketClient
from binance.spot import Spot as Client
import time
import os
import json
import certifi
import config
import datetime
import arbitrage_db as db
os.environ['SSL_CERT_FILE'] = certifi.where()
spot_client = Client(base_url="https://api.binance.com")

with open("arbitrage_opportunities.json", "r") as arb_file:
    arbitrage_opportunities = json.load(arb_file)

with open('tickers_start_info.json', 'r') as ticker_prices_file:
    config.tickers_start_info = json.load(ticker_prices_file)

ws_client = WebsocketClient()
ws_client.start()


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
    with open("trading_pairs.json", "r") as data_file:
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
    with open("arbitrage_opportunities.json", "w") as triang_file:
        json.dump(combinations, triang_file)


def get_actual_trading_pairs():
    base_and_quote_asset = []
    tickers = []
    exc_data = spot_client.exchange_info()["symbols"]
    for ticker in exc_data:
        if ticker["status"] != "BREAK":
            base_and_quote_asset.append([ticker["baseAsset"], ticker["quoteAsset"]])
            tickers.append(ticker['symbol'])
    with open("trading_pairs.json", "w") as data_file:
        json.dump(base_and_quote_asset, data_file)
    with open("trading_tickers.json", "w") as tickers_file:
        json.dump(tickers, tickers_file)


def market_handler(message):
    try:
        config.tickers_start_info[message['s']] = {
            "ask_price": message['a'],
            "bid_price": message['b'],
            "ask_qty": message['A'],
            "bid_qty": message['B']
        }
    except Exception:
        pass


def calculate_profit():
    counter = len(arbitrage_opportunities)
    arb_op_count = 0
    try:
        time_start = datetime.datetime.utcnow()
        for bunch in arbitrage_opportunities:
            print(f"Проверка связки {bunch}")
            route = get_route(bunch)
            if route[0] == "sell":
                first_price = float(config.tickers_start_info[bunch['first']]['bid_price'])
                first_qty = float(config.base_qty * first_price)
                first_side = "sell"
                print(f"Продаем {first_qty} {bunch['first']} по цене {first_price}")
            elif route[0] == "buy":
                first_price = float(config.tickers_start_info[bunch['first']]['ask_price'])
                first_qty = float(config.base_qty / first_price)
                print(f"Покупаем {first_qty} {bunch['first']} по цене {first_price}")
                first_side = "buy"
            else:
                print("Invalid data (first ticker)")

            first_fee = calculate_fee(bunch['first'], first_side, first_qty)

            if route[1] == "sell":
                second_price = float(config.tickers_start_info[bunch['second']]['bid_price'])
                second_qty = float(first_qty * second_price)
                print(f"Продаем {second_qty} {bunch['second']} по цене {second_price}")
                second_side = "sell"
            elif route[1] == "buy":
                second_price = float(config.tickers_start_info[bunch['second']]['ask_price'])
                second_qty = float(first_qty / second_price)
                print(f"Покупаем {second_qty} {bunch['second']} по цене {second_price}")
                second_side = "buy"
            else:
                print("Invalid data (second ticker)")

            second_fee = calculate_fee(bunch['second'], second_side, second_qty)

            if route[2] == "sell":
                third_price = float(config.tickers_start_info[bunch['third']]['bid_price'])
                third_qty = float(second_qty * third_price)
                print(f"Продаем {third_qty} {bunch['third']} по цене {third_price}")
                third_side = "sell"
            elif route[2] == "buy":
                third_price = float(config.tickers_start_info[bunch['third']]['ask_price'])
                third_qty = float(second_qty / third_price)
                print(f"Покупаем {third_qty} {bunch['third']} по цене {third_price}")
                third_side = "buy"
            else:
                print("Invalid data (third ticker)")

            third_fee = calculate_fee(bunch['third'], third_side, third_qty)

            result_fee_amount = first_fee + second_fee + third_fee
            best_depth_prices = [
                {
                    "bids": [config.tickers_start_info[bunch['first']['bid_price']],
                             config.tickers_start_info[bunch['second']['bid_price']],
                             config.tickers_start_info[bunch['third']['bid_price']]],
                    "asks": [config.tickers_start_info[bunch['first']['ask_price']],
                             config.tickers_start_info[bunch['second']['ask_price']],
                             config.tickers_start_info[bunch['third']['ask_price']]]
                }
            ]
            best_depth_qty = [
                {
                    "bids": [config.tickers_start_info[bunch['first']['bid_qty']],
                             config.tickers_start_info[bunch['second']['bid_qty']],
                             config.tickers_start_info[bunch['third']['bid_qty']]],
                    "asks": [config.tickers_start_info[bunch['first']['ask_qty']],
                             config.tickers_start_info[bunch['second']['ask_qty']],
                             config.tickers_start_info[bunch['third']['ask_qty']]]
                }
            ]

            profit = third_qty - float(config.base_qty)
            profit_percentage = float(profit / config.base_qty * 100)
            if profit > config.profit:
                print(f"Есть арбитражное окно. Наш профит составит: {profit} {config.base}")
                is_arbitrage = 1
            else:
                is_arbitrage = 0
                print("Нет арбитражного окна")

            data_for_insert_into_db = (
                bunch,
                result_fee_amount,
                is_arbitrage,
                profit,
                profit_percentage,
                best_depth_prices,
                best_depth_qty,
                datetime.datetime.utcnow()
            )
            db.insert(data_for_insert_into_db)
            counter -= 1
            if counter == 0:
                ws_client.stop()
        time_delta = datetime.datetime.utcnow() - time_start
        print(time_delta)
        print(arb_op_count)
    except KeyError:
        print("KEY ERROR")


def get_route(bundle):
    global third_side, second_side, first_side
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
        third_side = "sell"
    elif bundle['third'].endswith(third_token):
        third_side = "buy"
    return first_side, second_side, third_side


def get_start_prices_and_qty():
    info = {}
    with open("trading_tickers.json", "r") as trading_tickers_file:
        trading_tickers = json.load(trading_tickers_file)

    for ticker in trading_tickers:
        ticker_info = spot_client.book_ticker(ticker)
        info[ticker] = {
            "ask_price": ticker_info['askPrice'],
            "bid_price": ticker_info['bidPrice'],
            "ask_qty": ticker_info['askQty'],
            "bid_qty": ticker_info['bidQty']
        }
    with open("tickers_start_info.json", "w") as json_file:
        json.dump(info, json_file)


def calculate_fee(ticker, side, qty):
    asset = spot_client.exchange_info(symbol=ticker)['symbols']
    if side == "sell":
        ticker_asset = asset[0]['quoteAsset']
    elif side == "buy":
        ticker_asset = asset[0]['baseAsset']

    if f'{ticker_asset}BTC' in config.tickers_start_info:
        price = config.tickers_start_info[f'{ticker_asset}BTC']['ask_price']
        fee_amount_btc = float(qty) * float(price)
    elif f'BTC{ticker_asset}' in config.tickers_start_info:
        price = config.tickers_start_info[f'BTC{ticker_asset}']['bid_price']
        fee_amount_btc = float(qty) / float(price)
    bnb_btc_price = config.tickers_start_info['BNBBTC']['ask_price']
    result_fee_amount = float(fee_amount_btc) * float(bnb_btc_price)
    return result_fee_amount


ws_client.book_ticker(
        id=1,
        callback=market_handler
    )

calculate_profit()
# base = "PORTO"
#
# data_1 = [{"PORTO": "TRY"}, ]
# data_2 = { "TRY": "EUR"}
# data_3 = { "EUR": "PORTO"}
#
# data_2_base_keys = [item[1] for item in data_1]
