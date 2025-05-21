from lumibot.entities import Asset
from lumibot.backtesting import CcxtBacktesting
from lumibot.strategies.strategy import Strategy
from datetime import datetime, timedelta
from colorama import Fore
from llm import get_recommendation
import random


class MLTrader(Strategy):
    def initialize(self, cash_at_risk: float = 0.7, coin: str = "BTC"):
        self.set_market("24/7")
        self.sleeptime = "1D"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk
        self.coin = coin

    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(
            Asset(symbol=self.coin, asset_type=Asset.AssetType.CRYPTO),
            quote=Asset(symbol="USD", asset_type="crypto"),
        )
        # Added this to handle missing prices
        if last_price == None:
            quantity = 0
        else:
            max_cash_to_risk = min(cash, cash * self.cash_at_risk)
            quantity = max_cash_to_risk / last_price
        return cash, last_price, quantity

    def get_dates(self):
        today = self.get_datetime()
        day_prior = today - timedelta(days=1)
        return today, day_prior

    def get_price_change(self, period_days):
        """Get price change over a specific period in days"""
        # Get current price
        current_price = self.get_last_price(
            Asset(symbol=self.coin, asset_type=Asset.AssetType.CRYPTO),
            quote=Asset(symbol="USD", asset_type="crypto")
        )

        # Get historical data using length instead of date range
        bars = self.get_historical_prices(
            Asset(symbol=self.coin, asset_type=Asset.AssetType.CRYPTO),
            period_days + 1,  # length parameter as int
            timestep="day",  # specify the timestep explicitly
            quote=Asset(symbol="USD", asset_type="crypto"),
            include_after_hours=True
        )

        # Bars object has a df property for the DataFrame
        if bars is None or bars.df.empty:
            return None

        # Get oldest price in the period
        oldest_price = bars.df.iloc[0]["close"]

        # Calculate percentage change
        if oldest_price > 0:
            percent_change = ((current_price - oldest_price) / oldest_price) * 100
            return percent_change
        return None

    def get_24h_change(self):
        return self.get_price_change(1)

    def get_7d_change(self):
        return self.get_price_change(7)

    def get_30d_change(self):
        return self.get_price_change(30)

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()
        today, day_prior = self.get_dates()
        positions = self.get_positions()
        get_24h_change = self.get_24h_change()
        get_7d_change = self.get_7d_change()
        get_30d_change = self.get_30d_change()
        btc_quantity = 0
        for position in positions:
            if position.asset.symbol == self.coin:
                btc_quantity = position.quantity
                break

        choice, confidence = get_recommendation(
            coin=self.coin, start_date=day_prior, end_date=today, cash=self.get_cash(), btc_quantity=btc_quantity, get_24h_change=get_24h_change, get_7d_change=get_7d_change, get_30d_change=get_30d_change, last_price=last_price
        )
        # choice = random.choice(["buy", "sell", "hold"])
        # confidence = random.random()
        print("Decision: ", choice, "Confidence: ", confidence)
        print("Cash: ", cash, "Quantity: ", btc_quantity)
        if last_price != None and quantity > 0:
            if cash > (quantity * last_price):
                if choice == "hold":
                    pass
                elif choice == "buy" and confidence >= 0.7:
                    if self.last_trade == "sell":
                        self.sell_all()
                    order = self.create_order(
                        Asset(symbol=self.coin, asset_type=Asset.AssetType.CRYPTO),
                        quantity,
                        "buy",
                        order_type="market",
                        quote=Asset(symbol="USD", asset_type="crypto"),
                    )
                    print(Fore.LIGHTMAGENTA_EX + str(order) + Fore.RESET)
                    self.submit_order(order)
                    self.last_trade = "buy"
                elif choice == "sell" and confidence >= 0.7:
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
                            order_type="market",
                            quote=Asset(symbol="USD", asset_type="crypto"),
                        )
                        print(Fore.LIGHTMAGENTA_EX + str(order) + Fore.RESET)
                        self.submit_order(order)
                        self.last_trade = "sell"


if __name__ == "__main__":
    start_date = datetime(2024, 7, 31)
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
        quote_asset=Asset(symbol="USD", asset_type=Asset.AssetType.CRYPTO),
        parameters={"cash_at_risk": 0.5, "coin": "BTC"},
        **kwargs,
    )
