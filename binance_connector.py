from binance.websocket.spot.websocket_client import SpotWebsocketClient as Client
import certifi
import os
os.environ['SSL_CERT_FILE'] = certifi.where()


def message_handler(message):
    print(message)


ws_client = Client()
ws_client.start()

ws_client.book_ticker(
    id=1,
    callback=message_handler
)


