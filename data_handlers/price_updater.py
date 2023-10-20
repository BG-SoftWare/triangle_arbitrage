import json
import os

import certifi
import click
from binance.websocket.spot.websocket_client import SpotWebsocketClient as WebsocketClient
from redis import Redis

os.environ['SSL_CERT_FILE'] = certifi.where()

ws_client = WebsocketClient(stream_url="wss://stream.binance.com:9443")

with open(".env", "r") as file:
    keys = file.readlines()

host_name = keys[5].split("=")[1].rstrip()
port = keys[6].split("=")[1].rstrip()
password = keys[7].split("=")[1].rstrip()
redis_client = Redis(host=host_name, port=port, password=password)


def price_handler(message):
    if "stream" in message.keys():
        ticker = message["stream"].split("@")[0].upper()
        redis_client.set(
            ticker,
            json.dumps({
                'bid_price': json.dumps(message["data"]["bids"]),
                'ask_price': json.dumps(message["data"]["asks"])
            })
        )


@click.command()
@click.argument("index")
def socket_listener(index):
    with open("source/divided_pairs_list.json", "r") as divided_file:
        params_for_subscribe = json.load(divided_file)
    ws_client.start()
    ws_client.live_subscribe(
        id=int(index),
        stream=params_for_subscribe[int(index)],
        callback=price_handler
    )


if __name__ == "__main__":
    socket_listener()
