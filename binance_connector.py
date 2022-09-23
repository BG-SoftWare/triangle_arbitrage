from binance.websocket.websocket_client import BinanceWebsocketClient as WebsocketClient
from binance.spot import Spot as Client
import certifi
import os
os.environ['SSL_CERT_FILE'] = certifi.where()
spot_client = Client(base_url="https://api.binance.com")

def message_handler(message):
    print(message)



# def price_extractor(response):
#     try:
#         top_bid_price, top_bid_qty = response["bids"][0]
#         top_ask_price, top_ask_qty = response["asks"][0]
#         print(top_bid_price, top_bid_qty)
#         print(top_ask_price, top_ask_qty)
#     except Exception:
#         print("Some exception")

#
# ws_client = Client()
# ws_client.start()

# ws_client.book_ticker(
#     id=1,
#     symbol="IOTABUSD",
#     callback=message_handler
# )
# ws_client.partial_book_depth(
#     symbol="ALPHABUSD",
#     id=1,
#     level=5,
#     speed=100,
#     callback=price_extractor
# )
#
# user_assets = ws_client.user_asset()

