from binance.spot import Spot as Client
import certifi
import os
import re
os.environ['SSL_CERT_FILE'] = certifi.where()


spot_client = Client(base_url="https://api.binance.com")

pairs = []
special_pairs = ["BNBBUSD", "BTCBUSD", "BUSDUSDT", "ETHBUSD", "AUDBUSD", "BUSDBIDR", "BUSDBRL", "EURBUSD", "GBPBUSD",
              "BUSDRUB", "BUSDTRY", "BUSDUAH", "BUSDNGN"]

symbols = spot_client.exchange_info()["symbols"]

for symbol in symbols:
    if re.findall(r'\bBUSD', symbol["symbol"]) or re.findall(r'BUSD\b', symbol["symbol"]):
        pairs.append(symbol["symbol"])

regular_pairs = [pair for pair in pairs if pair not in special_pairs]

with open("regular_pairs.txt", "a") as txt_file:
    for pair in regular_pairs:
        txt_file.write(pair + "\n")
