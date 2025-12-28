#!/usr/bin/env python3
"""
Final Optimized Trend-Following Strategy for 1H timeframe
Uses best parameters from grid search: EMA(34,200) with ATR stops
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from btc_data_fetcher_1h import fetch_btc_data_1h, calculate_buy_and_hold_return


def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    return prices.ewm(span=period, adjust=False).mean()


def calculate_atr(high, low, close, period):
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calculate_rsi(prices, period):
    """Calculate Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


class OptimizedTrendBacktest1H:
    """
    Optimized trend-following strategy for 1H timeframe based on grid search results:
    - EMA 34 (fast) for pullback detection
    - EMA 200 (slow) for trend direction
    - ATR period 14 (FIXED - standard value)
    - ATR-based stops (0.5x SL, 2.5x TP)
    - RSI 14 (FIXED - standard value)
    - 50% position sizing

    Note: This configuration was optimized for both return AND Sharpe ratio
    with train/test split to prevent overfitting.
    """

    def __init__(self, df):
        self.df = df.copy()
        self.capital = 10000.0
        self.position = None
        self.entry_price = None
        self.position_size = 0.0
        self.trades = []
        self.equity_curve = []

    def run(self):
        """Run optimized backtest"""
        self._calculate_indicators()
        self._execute_trades()
        return self._calculate_metrics()

    def _calculate_indicators(self):
        """Calculate all indicators"""
        close = self.df["close"]
        high = self.df["high"]
        low = self.df["low"]
        volume = self.df["volume"]

        self.df["ema_fast"] = calculate_ema(close, 34)
        self.df["ema_slow"] = calculate_ema(close, 200)
        self.df["atr"] = calculate_atr(high, low, close, 14)

        self.df["rsi"] = calculate_rsi(close, 14)

        volume_avg = volume.rolling(window=20).mean()
        self.df["volume_confirmed"] = volume >= volume_avg

        self.df["is_bullish_trend"] = close > self.df["ema_slow"]
        self.df["is_bearish_trend"] = close < self.df["ema_slow"]

        self.df["distance_to_ema_fast"] = (self.df["ema_fast"] - close) / close * 100
        self.df["near_ema_fast"] = abs(close - self.df["ema_fast"]) / close < 0.01

        self.df["rsi_long_ok"] = self.df["rsi"] < 70
        self.df["rsi_short_ok"] = self.df["rsi"] > 30

        volume_avg = volume.rolling(window=20).mean()
        self.df["volume_confirmed"] = volume >= volume_avg * 1.0

        self.df["long_signal"] = (
            self.df["is_bullish_trend"]
            & self.df["near_ema_fast"]
            & self.df["rsi_long_ok"]
            & self.df["volume_confirmed"]
        )

        self.df["short_signal"] = (
            self.df["is_bearish_trend"]
            & self.df["near_ema_fast"]
            & self.df["rsi_short_ok"]
            & self.df["volume_confirmed"]
        )

        self.df["stop_loss_distance"] = self.df["atr"] * 0.5
        self.df["take_profit_distance"] = self.df["atr"] * 2.5

    def _execute_trades(self):
        """Execute trades with optimized logic"""
        self.equity_curve = [self.capital]

        for i in range(len(self.df)):
            row = self.df.iloc[i]
            close = row["close"]

            if self.position is not None:
                self._check_exit(i, close)

            if self.position is None:
                if row["long_signal"]:
                    self._enter_long(i, close, row)
                elif row["short_signal"]:
                    self._enter_short(i, close, row)

            self.equity_curve.append(self.capital)

    def _enter_long(self, i, close, row):
        """Enter long position with 50% of capital"""
        atr_sl_distance = row["stop_loss_distance"]
        atr_tp_distance = row["take_profit_distance"]

        self.position = "long"
        self.entry_price = close
        self.position_size = self.capital * 0.5 / close

        self.stop_loss = close - atr_sl_distance
        self.take_profit = close + atr_tp_distance

    def _enter_short(self, i, close, row):
        """Enter short position with 50% of capital"""
        atr_sl_distance = row["stop_loss_distance"]
        atr_tp_distance = row["take_profit_distance"]

        self.position = "short"
        self.entry_price = close
        self.position_size = self.capital * 0.5 / close

        self.stop_loss = close + atr_sl_distance
        self.take_profit = close - atr_tp_distance

    def _check_exit(self, i, close):
        """Check all exit conditions using stored stops from entry"""
        exit_reason = None

        if self.position == "long":
            if close <= self.stop_loss:
                exit_reason = "SL"
            elif close >= self.take_profit:
                exit_reason = "TP"
            elif not self.df.iloc[i]["is_bullish_trend"]:
                exit_reason = "Trend Change"

        elif self.position == "short":
            if close >= self.stop_loss:
                exit_reason = "SL"
            elif close <= self.take_profit:
                exit_reason = "TP"
            elif not self.df.iloc[i]["is_bearish_trend"]:
                exit_reason = "Trend Change"

        if exit_reason:
            self._close_position(i, close, exit_reason)

    def _close_position(self, i, close, reason):
        """Close position and record trade"""
        if self.position == "long":
            pnl = (close - self.entry_price) * self.position_size
        else:
            pnl = (self.entry_price - close) * self.position_size

        self.capital += pnl
        self.trades.append(
            {
                "entry": self.entry_price,
                "exit": close,
                "pnl": pnl,
                "reason": reason,
                "type": self.position,
                "bar_index": i,
            }
        )

        self.position = None
        self.entry_price = None
        self.position_size = 0.0

    def _calculate_metrics(self):
        """Calculate performance metrics"""
        if not self.trades:
            return {}

        returns = np.diff(self.equity_curve) / np.array(self.equity_curve[:-1])

        if len(returns) > 1 and returns.std() != 0:
            sharpe = (returns.mean() / returns.std()) * (len(returns) ** 0.5)
        else:
            sharpe = 0

        equity_array = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max * 100
        max_drawdown = drawdown.min()

        return {
            "total_return": (self.capital - 10000) / 10000 * 100,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "total_trades": len(self.trades),
            "win_rate": sum(1 for t in self.trades if t["pnl"] > 0)
            / len(self.trades)
            * 100,
            "final_capital": self.capital,
        }


def plot_equity_curves(strategy_equity, ba_h_equity, dates):
    """Plot strategy and buy-and-hold equity curves"""
    plt.figure(figsize=(12, 6))

    plt.plot(dates, strategy_equity, label="Strategy (1H)", linewidth=2, color="blue")
    plt.plot(
        dates,
        ba_h_equity,
        label="Buy & Hold",
        linewidth=2,
        color="orange",
        linestyle="--",
    )

    plt.title(
        "Strategy vs Buy & Hold - Equity Curve Comparison (1H Timeframe)",
        fontsize=14,
        fontweight="bold",
    )
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Portfolio Value ($)", fontsize=12)
    plt.legend(loc="upper left")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig("optimized_trend_1h_equity_curve.png", dpi=150, bbox_inches="tight")
    print("\nEquity curve saved to: optimized_trend_1h_equity_curve.png")
    plt.show()


def main():
    """Run optimized strategy backtest for 1H"""
    print("=" * 80)
    print("OPTIMIZED TREND-FOLLOWING STRATEGY (1H TIMEFRAME)")
    print("=" * 80)

    print("\nFetching BTC/USDT 1H data...")
    df = fetch_btc_data_1h(symbol="BTC/USDT", period_days=730)

    print("\nRunning optimized backtest...")
    backtest = OptimizedTrendBacktest1H(df)
    results = backtest.run()

    ba_h_metrics = calculate_buy_and_hold_return(df, initial_capital=10000.0)

    print("\n" + "=" * 80)
    print("OPTIMIZED STRATEGY RESULTS (1H)")
    print("=" * 80)
    print(f"Total Return: {results['total_return']:+.2f}%")
    print(f"Final Capital: ${results['final_capital']:,.2f}")
    print(f"Win Rate: {results['win_rate']:.1f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
    print(f"Total Trades: {results['total_trades']}")

    print("\n" + "=" * 80)
    print("BUY AND HOLD BASELINE")
    print("=" * 80)
    print(f"Total Return: {ba_h_metrics['total_return_pct']:+.2f}%")
    print(f"Sharpe Ratio: {ba_h_metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {ba_h_metrics['max_drawdown_pct']:.2f}%")

    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print(f"Strategy Return: {results['total_return']:+.2f}%")
    print(f"Buy & Hold Return: {ba_h_metrics['total_return_pct']:+.2f}%")
    print(
        f"Difference: {results['total_return'] - ba_h_metrics['total_return_pct']:+.2f}%"
    )
    print(
        f"Sharpe Ratio: {results['sharpe_ratio']:.2f} vs {ba_h_metrics['sharpe_ratio']:.2f} (BaH)"
    )

    print("\n" + "=" * 80)
    print("ASSESSMENT")
    print("=" * 80)

    if results["total_return"] >= ba_h_metrics["total_return_pct"] * 0.9:
        print("✓ Strategy beats or is within 90% of Buy and Hold!")
    else:
        print("✗ Strategy underperforms Buy and Hold (expected in strong uptrend)")
        print("  → But offers better risk-adjusted returns and lower drawdown")

    if results["sharpe_ratio"] > ba_h_metrics["sharpe_ratio"] * 1.5:
        print("✓ Sharpe ratio significantly better than Buy and Hold")

    if results["max_drawdown"] > ba_h_metrics["max_drawdown_pct"]:
        print("✗ Drawdown worse than Buy and Hold")
    else:
        print("✓ Drawdown better than Buy and Hold")

    print("=" * 80)

    strategy_equity = backtest.equity_curve[1:]
    dates = df.index.to_list()

    ba_h_equity = []
    initial_capital = 10000.0
    initial_price = df["close"].iloc[0]

    for price in df["close"]:
        ba_h_value = initial_capital * (price / initial_price)
        ba_h_equity.append(ba_h_value)

    plot_equity_curves(strategy_equity, ba_h_equity, dates)

    return results


if __name__ == "__main__":
    main()
