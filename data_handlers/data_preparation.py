import json
import os
import sys

import requests

import config


class DataPreparation:
    if os.path.exists("../source"):
        pass
    else:
        os.mkdir("../source")

    def __init__(self):
        self.base_token = config.base_token.upper()
        self.arbitrage_combinations = []
        self.divided_pairs_list = []
        self.unique_pairs = []
        self.trading_pairs = {}

    def get_actual_trading_pairs(self):
        try:
            exchange_data = requests.get("https://api.binance.com/api/v3/exchangeInfo").json()["symbols"]
        except ConnectionError:
            sys.exit()

        for ticker in exchange_data:
            if ticker["status"] != "BREAK" and ticker["isSpotTradingAllowed"]:
                self.trading_pairs[ticker['symbol']] = {
                    'base_asset': ticker["baseAsset"],
                    'quote_asset': ticker["quoteAsset"],
                    'base_asset_precision': ticker["baseAssetPrecision"],
                    'quote_asset_precision': ticker["quoteAssetPrecision"]
                }
                for symbol_filter in ticker['filters']:
                    keys = list(symbol_filter.keys())
                    values = list(symbol_filter.values())
                    updating = {values[0].lower(): dict(zip(keys[1:], values[1:]))}
                    self.trading_pairs[ticker['symbol']].update(updating)
        with open("../source/trading_pairs.json", "w") as data_file:
            json.dump(self.trading_pairs, data_file)

    def get_triangle_combination(self):
        for pair_first in self.trading_pairs.values():
            if self.base_token == pair_first["base_asset"]:
                second_token = pair_first["quote_asset"]
                first = f"{self.base_token}{second_token}"
            elif self.base_token == pair_first["quote_asset"]:
                second_token = pair_first["base_asset"]
                first = f"{second_token}{self.base_token}"
            else:
                continue
            for pair_second in self.trading_pairs.values():
                if second_token == pair_second["base_asset"]:
                    third_token = pair_second["quote_asset"]
                    second = f"{second_token}{third_token}"
                elif second_token == pair_second["quote_asset"]:
                    third_token = pair_second["base_asset"]
                    second = f"{third_token}{second_token}"
                else:
                    continue
                for pair_third in self.trading_pairs.values():
                    if third_token == pair_third["base_asset"] and self.base_token == pair_third["quote_asset"]:
                        third = f"{third_token}{self.base_token}"
                    elif self.base_token == pair_third["base_asset"] and third_token == pair_third["quote_asset"]:
                        third = f"{self.base_token}{third_token}"
                    else:
                        continue
                    combination = {
                        "first": first,
                        "second": second,
                        "third": third
                    }
                    routes = self.__get_route(combination)

                    data = {
                        "combination": combination,
                        "routes": routes
                    }
                    self.arbitrage_combinations.append(data)

        with open(f"source/arbitrage_combinations_{config.base_token.lower()}.json", "w") as combination_file:
            json.dump(self.arbitrage_combinations, combination_file)

    def __get_route(self, combination):
        second_token = str()
        third_token = str()
        first_side = str()
        second_side = str()
        third_side = str()

        if self.base_token.upper() == self.trading_pairs[combination["first"]]["base_asset"]:
            first_side = "sell"
            second_token = self.trading_pairs[combination["first"]]["quote_asset"]
        elif self.base_token.upper() == self.trading_pairs[combination["first"]]["quote_asset"]:
            first_side = "buy"
            second_token = self.trading_pairs[combination["first"]]["base_asset"]

        if second_token == self.trading_pairs[combination["second"]]["base_asset"]:
            second_side = "sell"
            third_token = self.trading_pairs[combination["second"]]["quote_asset"]
        elif second_token == self.trading_pairs[combination["second"]]["quote_asset"]:
            second_side = "buy"
            third_token = self.trading_pairs[combination["second"]]["base_asset"]

        if third_token == self.trading_pairs[combination["third"]]["base_asset"]:
            third_side = "sell"
        elif third_token == self.trading_pairs[combination["third"]]["quote_asset"]:
            third_side = "buy"

        return first_side, second_side, third_side

    @staticmethod
    def get_divided_list(pairs):
        len_lists = 100
        divided_pairs_list = [pairs[index:index + len_lists] for index in range(0, len(pairs), len_lists)]
        with open(f"source/divided_pairs_list.json", "w") as divided_file:
            json.dump(divided_pairs_list, divided_file)

    def create_params(self):
        params = []
        for element in self.trading_pairs.keys():
            first_param_string = f"{element.lower()}@depth5@100ms"
            params.append(first_param_string)
        return params


if __name__ == "__main__":
    data_preparation = DataPreparation()
    data_preparation.get_actual_trading_pairs()
    data_preparation.get_triangle_combination()
    params_for_subscribe = data_preparation.create_params()
    data_preparation.get_divided_list(params_for_subscribe)
