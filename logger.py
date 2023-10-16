import logging
from logging.handlers import TimedRotatingFileHandler
from calendar import monthrange
import os
import datetime


if os.path.exists(f"logs/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}"):
    pass
else:
    os.makedirs(f"logs/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}")

filename = f"logs/{datetime.datetime.now().strftime('%Y')}/{datetime.datetime.now().strftime('%m')}/" \
            f"triangle_arbitrage.log"

day_in_month = monthrange(int(datetime.datetime.now().strftime('%Y')),
                          int(datetime.datetime.now().strftime('%m')))[1]

time_rotating_handler = TimedRotatingFileHandler(filename, when="midnight", interval=1, backupCount=day_in_month + 1)
time_rotating_handler.suffix = '%d_%m_%Y'
stream_handler = logging.StreamHandler()
logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] - %(asctime)s - %(name)s - %(threadName)s - %(message)s',
                    handlers=[time_rotating_handler, stream_handler])
logging.getLogger("binance").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name):
    return logging.getLogger(name)
