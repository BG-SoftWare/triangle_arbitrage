import json
from binance.websocket.spot.websocket_client import SpotWebsocketClient as WebsocketClient
from logging.handlers import TimedRotatingFileHandler
from calendar import monthrange
import logging
import os
import certifi
import datetime
import click
from redis import Redis

os.environ['SSL_CERT_FILE'] = certifi.where()


if os.path.exists(f"logs/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}"):
    pass
else:
    os.makedirs(f"logs/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}")

filename = f"logs/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}/" \
            f"price_updater_{datetime.datetime.now().strftime('%d_%m_%Y')}.log"

day_in_month = monthrange(int(datetime.datetime.now().strftime('%Y')), int(datetime.datetime.now().strftime('%m')))[1]

time_rotating_handler = TimedRotatingFileHandler(filename, when="midnight", interval=1, backupCount=day_in_month + 1)
stream_handler = logging.StreamHandler()

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s',
                    handlers=[time_rotating_handler, stream_handler])
logger = logging.getLogger("PRICE UPDATER")

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
    elif 'result' in message.keys() and 'id' in message.keys():
        logger.info(f"Socket id {message['id']} was run. Waiting information")
    else:
        logger.error("Some Error")


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
