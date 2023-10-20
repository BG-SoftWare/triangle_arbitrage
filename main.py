from trading.triangle_arbitrage import TriangleArbitrage

if __name__ == "__main__":
    bot = TriangleArbitrage()
    while True:
        bot.start()
