from binance.websocket.spot.websocket_client import SpotWebsocketClient as Client
from binance.websocket.websocket_client import BinanceWebsocketClient as WebsocketClient
import certifi
import os
import json
import datetime
os.environ['SSL_CERT_FILE'] = certifi.where()


with open("busd_pairs.json", "r") as json_file:
    busd_pairs = json.load(json_file)


def message_handler(message):
    print(message)


def price_extractor(response):
    try:
        top_bid_qty, top_bid_price = response["bids"][0]
        top_ask_qty, top_ask_price = response["asks"][0]
        print(top_bid_price)
        print(top_ask_price)
    except Exception as e:
        print("Some exception")


ws_client = Client()
ws_client.start()

ws_client.partial_book_depth(
    symbol="ETHBUSD",
    id=1,
    level=5,
    speed=100,
    callback=price_extractor
)


def get_route(ticker, base):
    if ticker.startwith(base):
        return "SELL"
    elif ticker.endwith(base):
        return "BUY"
    else:
        print("Invalid ticker!")
