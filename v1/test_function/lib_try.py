from lumibot.entities import Asset
from lumibot.backtesting import CcxtBacktesting
from lumibot.strategies.strategy import Strategy
from datetime import datetime
from colorama import Fore
import random


class MLTrader(Strategy):

    def initialize(self, cash_at_risk: float = 0.2, coin: str = "BTC"):
        self.set_market("24/7")
        self.sleeptime = "1D"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk
        self.coin = coin

    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(
            Asset(symbol=self.coin, asset_type=Asset.AssetType.CRYPTO),
            quote=Asset(symbol="AUD", asset_type="crypto"),
        )
        # Added this to handle missing prices
        if last_price == None:
            quantity = 0
        else:
            max_cash_to_risk = min(cash, cash * self.cash_at_risk)
            quantity = max_cash_to_risk / last_price
        return cash, last_price, quantity

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()

        if last_price != None and quantity > 0:
            if cash > (quantity * last_price):
                choice = random.choice([0, 1, 2])

                if choice == 0:  # Hold
                    pass
                elif choice == 1:  # Buy
                    if self.last_trade == "sell":
                        self.sell_all()
                    order = self.create_order(
                        Asset(symbol=self.coin, asset_type=Asset.AssetType.CRYPTO),
                        quantity,
                        "buy",
                        type="market",
                        quote=Asset(symbol="AUD", asset_type="crypto"),
                    )
                    print(Fore.LIGHTMAGENTA_EX + str(order) + Fore.RESET)
                    self.submit_order(order)
                    self.last_trade = "buy"
                elif choice == 2:  # Sell
                    positions = self.get_positions()
                    has_btc = False
                    for position in positions:
                        if position.asset.symbol == self.coin:
                            has_btc = True
                            break

                    if has_btc and self.last_trade == "buy":
                        self.sell_all()
                    elif has_btc:
                        order = self.create_order(
                            Asset(symbol=self.coin, asset_type=Asset.AssetType.CRYPTO),
                            quantity,
                            "sell",
                            type="market",
                            quote=Asset(symbol="AUD", asset_type="crypto"),
                        )
                        print(Fore.LIGHTMAGENTA_EX + str(order) + Fore.RESET)
                        self.submit_order(order)
                        self.last_trade = "sell"


if __name__ == "__main__":
    start_date = datetime(2024, 5, 14)
    end_date = datetime(2025, 5, 15)
    exchange_id = "kraken"
    kwargs = {
        "exchange_id": exchange_id,
    }
    CcxtBacktesting.MIN_TIMESTEP = "day"

    results, strat_obj = MLTrader.run_backtest(
        CcxtBacktesting,
        start_date,
        end_date,
        benchmark_asset=Asset(symbol="BTC", asset_type=Asset.AssetType.CRYPTO),
        quote_asset=Asset(symbol="AUD", asset_type=Asset.AssetType.CRYPTO),
        parameters={"cash_at_risk": 0.5, "coin": "BTC"},
        **kwargs,
    )