import backtrader as bt
import ccxt
import pandas as pd
import pyfolio as pf
import matplotlib

matplotlib.use("Agg")
from datetime import datetime, timedelta
from typing import Optional


class EMAStrategy(bt.Strategy):
    params = (
        ("ema_period", 100),
        ("stop_loss_pct", 0.02),
        ("cooldown_minutes", 30),
    )

    def __init__(self):
        self.ema = bt.indicators.EMA(self.data.close, period=self.params.ema_period)
        self.ema.plotinfo.plot = True
        self.ema.plotinfo.name = f"EMA{self.params.ema_period}"
        self.ema.plotinfo.color = "blue"
        self.ema.plotinfo.linewidth = 2

        self.last_trade_exit_time: Optional[datetime] = None
        self.stop_order = None
        self.tp_order = None
        self.buy_order = None
        self.position_open = False

    def next(self):
        current_time = self.data.datetime.datetime(0)

        if self.last_trade_exit_time:
            time_since_exit = current_time - self.last_trade_exit_time
            if time_since_exit < timedelta(minutes=self.params.cooldown_minutes):
                return

        if not self.position_open and not self.position:
            if self.ema[0] > self.data.open[0]:
                entry_price = self.data.close[0]
                stop_loss = entry_price * (1 - self.params.stop_loss_pct)
                take_profit = entry_price * (1 + self.params.stop_loss_pct * 2)

                self.buy_order = self.buy(size=1)
                self.stop_order = self.sell(
                    size=1, exectype=bt.Order.Stop, price=stop_loss
                )
                self.tp_order = self.sell(
                    size=1, exectype=bt.Order.Limit, price=take_profit
                )
                self.position_open = True

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                pass
            elif order.issell():
                self.cancel_other_orders(order)
                self.position_open = False
                self.last_trade_exit_time = self.data.datetime.datetime(0)

        if order.status in [order.Cancelled, order.Rejected, order.Margin]:
            if order == self.buy_order:
                self.position_open = False
                self.cancel(self.stop_order)
                self.cancel(self.tp_order)

    def cancel_other_orders(self, executed_order):
        if (
            executed_order == self.stop_order
            and self.tp_order
            and self.tp_order.alive()
        ):
            self.cancel(self.tp_order)
        elif (
            executed_order == self.tp_order
            and self.stop_order
            and self.stop_order.alive()
        ):
            self.cancel(self.stop_order)


def fetch_btc_data() -> pd.DataFrame:
    exchange = ccxt.binance()

    end_time = int(datetime.now().timestamp() * 1000)
    start_time = end_time - (2 * 365 * 24 * 60 * 60 * 1000)

    all_ohlcv = []
    current_time = start_time

    while current_time < end_time:
        limit = 1000
        ohlcv = exchange.fetch_ohlcv(
            "BTC/USDT", timeframe="1h", since=current_time, limit=limit
        )

        if len(ohlcv) == 0:
            break

        all_ohlcv.extend(ohlcv)
        current_time = ohlcv[-1][0] + 1

    if len(all_ohlcv) == 0:
        raise ValueError("No data fetched from Binance")

    df = pd.DataFrame(
        all_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)

    return df


def run_backtest():
    cerebro = bt.Cerebro()

    data = fetch_btc_data()
    data_feed = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data_feed)

    cerebro.addstrategy(EMAStrategy)
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name="pyfolio")
    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(commission=0.001)

    start_value = cerebro.broker.getvalue()
    strategies = cerebro.run()
    end_value = cerebro.broker.getvalue()

    print(f"Starting Portfolio Value: {start_value:.2f}")
    print(f"Final Portfolio Value: {end_value:.2f}")

    strategy = strategies[0]
    pyfoliozer = strategy.analyzers.getbyname("pyfolio")

    returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()

    print("\nGenerating PyFolio tear sheet...\n")
    try:
        pf.create_full_tear_sheet(
            returns,
            positions=positions,
            transactions=transactions,
            round_trips=True,
        )
    except Exception as e:
        print(f"Error generating full tear sheet: {e}")
        print("\nGenerating basic tear sheet without round trips...\n")
        pf.create_full_tear_sheet(
            returns,
            positions=positions,
            transactions=transactions,
            round_trips=False,
        )

    print("\nGenerating strategy plot...\n")
    figs = cerebro.plot(
        style="candlestick",
        barup="green",
        bardown="red",
        volume=True,
        savefig="backtrader_strategy_plot.png",
    )
    matplotlib.pyplot.close("all")


if __name__ == "__main__":
    run_backtest()
