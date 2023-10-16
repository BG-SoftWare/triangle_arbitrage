import json
import os
import time
import uuid
from ast import literal_eval
from decimal import Decimal
from queue import Queue
from threading import Event, Thread, Lock

import certifi
from binance.spot import Spot as Client
from binance.websocket.spot.websocket_client import SpotWebsocketClient as WebsocketClient
from redis import Redis

import config
import db_connector
import logger

os.environ['SSL_CERT_FILE'] = certifi.where()

with open(".env", "r") as file:
    keys = file.readlines()

api_key = keys[0].split("=")[1].rstrip()
secret_key = keys[1].split("=")[1].rstrip()
host_name = keys[5].split("=")[1].rstrip()
port = keys[6].split("=")[1].rstrip()
password = keys[7].split("=")[1].rstrip()


class TradingBot:
    def __init__(self):
        self.logger = logger.get_logger("TRADING BOT")
        self.base_token = config.base_token
        self._spot_client = Client(api_key, secret_key, base_url="https://api.binance.com")
        self.listen_key = self.__get_listen_key()
        self.__update_listen_key(self.listen_key, 30 * 60)
        self._ws_client = WebsocketClient(stream_url="wss://stream.binance.com:9443")
        self.listen_key_create_time = 0
        self.db = db_connector.DatabaseConnector(self.logger)
        self.redis_client = Redis(host=host_name, port=port, password=password, db=0)
        self.insert_queue = Queue()
        self.lock = Lock()
        self.base_balance = self.get_base_asset_balance()

        self.trade_flag = False
        self.user_data()
        self.order_status = None
        self.need_rollback = False
        self.start = False
        self.orders_quantities = {}
        self.order_id = None
        self.side = None
        self._order_creation_time = None
        self.ticker = None
        self.price = None

    def create_limit_order(self, ticker: str, side: str, quantity: Decimal, price: Decimal):
        self.logger.info(f"Trying create a new order.")
        self.order_id = uuid.uuid4()
        self.trade_flag = False
        try:
            response = self._spot_client.new_order(
                symbol=ticker,
                side=side,
                type="LIMIT",
                price=price,
                timeInForce="GTC",
                quantity=quantity,
                newClientOrderId=self.order_id
            )

            self.logger.info(response)
            if response["status"] == "FILLED":

                self.trade_flag = True
                self.need_rollback = False
                return response
            elif response['status'] == "NEW":
                self._order_creation_time = response['transactTime']
                self.ticker = response['symbol']
                self.price = Decimal(response['price'])
                self.side = response['side']
                timer_thread = Thread(target=self.need_rollback_controller, name="Timer-Th", daemon=True)
                timer_thread.start()
        except Exception:
            self.logger.error("Order not issued", exc_info=True)

    def need_rollback_controller(self):
        start_time = self._order_creation_time
        stop_time = start_time + config.minute_for_waiting_to_cancel_order * 60 * 1000
        current_price = 0

        self.logger.info("Waiting for order to close")
        try:
            while True:
                now_time = int(time.time() * 1000)
                if self.side.upper() == "BUY":
                    current_price = Decimal(literal_eval(json.loads(self.redis_client.get(self.ticker).
                                                                    decode("utf-8"))["ask_price"])[0][0])
                elif self.side.upper() == "SELL":
                    current_price = Decimal(literal_eval(json.loads(self.redis_client.get(self.ticker).
                                                                    decode("utf-8"))["bid_price"])[0][0])

                if self.order_status == "FILLED":
                    self.logger.info("The order has been FILLED. Creating the next order")
                    with self.lock:
                        self.trade_flag = True
                        self.need_rollback = False
                    break
                elif ((abs(self.price - current_price) / self.price) * 100 >=
                      Decimal(config.price_delta_percent_to_cancel_order)):
                    self.logger.info(f"The price has changed by more than {config.price_delta_percent_to_cancel_order} "
                                     f"percent. Doing a rollback.")
                    with self.lock:
                        self.trade_flag = False
                        self.need_rollback = True
                    break
                elif now_time >= stop_time:
                    self.logger.warning(f"The order did not close within {config.minute_for_waiting_to_cancel_order} "
                                        f"minutes. Doing a rollback.")
                    with self.lock:
                        self.trade_flag = False
                        self.need_rollback = True
                    break
        except Exception:
            self.logger.error("Rollback controller function terminated unexpectedly.", exc_info=True)

    def cancel_order(self, ticker: str, order_id: str):
        cancel_order = self._spot_client.cancel_order(
            symbol=ticker,
            origClientOrderId=order_id
        )
        return cancel_order

    def get_base_asset_balance(self):
        base_balance = list(filter(
            lambda balance: balance["asset"] == self.base_token.upper(),
            self._spot_client.account()['balances']))[0]["free"]
        return Decimal(base_balance)

    def _user_data_handler(self, message):
        self.logger.info(message)
        if 'e' in message:
            try:
                if message['e'] == 'executionReport':
                    if self.order_id == message['c']:
                        self._event_time = message['E']
                        self.order_status = message['X']
                        self.side = message['S']

                        if self.order_status == "FILLED":
                            self.trade_flag = True
                            self.need_rollback = False

                        data_to_insert = {
                            'symbol': message["s"],
                            'order_id': str(self.order_id),
                            'order_status': self.order_status,
                            'quantity': message['q'],
                            'price': message["p"],
                            'fee_asset': message["N"],
                            'fee_amount': message["n"],
                            'quote_order_qty': message['Z'],
                            'order_creation_time': message["O"],
                            'transaction_time': message["T"]
                        }
                        data = {"table_name": "trading", "data": data_to_insert}
                        self.insert_queue.put(data)
            except Exception:
                self.logger.error("User Data Stream handler returned an error. "
                                  "The message about EXECUTION REPORT not processed", exc_info=True)
            if message['e'] == 'outboundAccountPosition':
                data_to_insert = {
                    'base_asset': message['B'][0]['a'],
                    'base_balance': message['B'][0]['f'],
                    'quote_asset': message['B'][1]['a'],
                    'quote_balance': message['B'][1]['f']
                }
                if data_to_insert["base_asset"].upper() == self.base_token:
                    self.base_balance = data_to_insert["base_balance"]
                elif data_to_insert["quote_asset"].upper() == self.base_token:
                    self.base_balance = data_to_insert["quote_balance"]

                data = {"table_name": "balance_exchanges", "data": data_to_insert}
                self.insert_queue.put(data)
            elif message['e'] == 'balanceUpdate':
                data_to_insert = {
                    'asset': message['a'],
                    'balance_delta': message['d'],
                    'update_time': message['T']
                }
                data = {"table_name": "wallet_update", "data": data_to_insert}
                self.insert_queue.put(data)
            insert_thread = Thread(target=self.db.insert_data, args=(self.insert_queue,), name="Insert-Th",
                                   daemon=False)
            insert_thread.start()

        if "result" in message and "id" in message:
            self.logger.info("Socket started")
            self.start = True

    def user_data(self):
        self._ws_client.name = "UserDataStream-Th"
        self._ws_client.start()
        self._ws_client.user_data(
            listen_key=self.listen_key,
            id=1,
            callback=self._user_data_handler
        )

    def __get_listen_key(self):
        return self._spot_client.new_listen_key()['listenKey']

    def __update_listen_key(self, listen_key, interval):
        stopped = Event()

        def loop():
            while not stopped.wait(interval):
                self._spot_client.renew_listen_key(listenKey=listen_key)

        Thread(target=loop).start()
        return stopped.set
