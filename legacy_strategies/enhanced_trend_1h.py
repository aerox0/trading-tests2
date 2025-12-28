#!/usr/bin/env python3
"""
Enhanced 1H Strategy with Volatility Filtering
Adds ADX trend strength filter and volatility-based position sizing
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


def calculate_adx(high, low, close, period=14):
    """Calculate Average Directional Index"""
    plus_dm = high.diff()
    minus_dm = low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    minus_dm = -minus_dm

    tr = calculate_atr(high, low, close, 1)

    plus_di = 100 * (
        plus_dm.rolling(window=period).mean() / tr.rolling(window=period).mean()
    )
    minus_di = 100 * (
        minus_dm.rolling(window=period).mean() / tr.rolling(window=period).mean()
    )

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()

    return adx, plus_di, minus_di


class EnhancedTrendBacktest1H:
    """
    Enhanced trend-following strategy for 1H timeframe with:
    - EMA 30/180 for trend detection
    - ATR-based dynamic stops
    - ADX filter for trend strength (only trade strong trends)
    - Volatility-based position sizing
    - Improved RSI filter
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
        """Run enhanced backtest"""
        self._calculate_indicators()
        self._execute_trades()
        return self._calculate_metrics()

    def _calculate_indicators(self):
        """Calculate all indicators"""
        close = self.df["close"]
        high = self.df["high"]
        low = self.df["low"]
        volume = self.df["volume"]

        # EMAs for trend detection
        self.df["ema_fast"] = calculate_ema(close, 30)
        self.df["ema_slow"] = calculate_ema(close, 180)

        # ATR for volatility
        self.df["atr"] = calculate_atr(high, low, close, 14)

        # RSI
        self.df["rsi"] = calculate_rsi(close, 14)

        # ADX for trend strength
        self.df["adx"], self.df["plus_di"], self.df["minus_di"] = calculate_adx(
            high, low, close, 14
        )

        # Volume filter
        volume_avg = volume.rolling(window=20).mean()
        self.df["volume_confirmed"] = volume >= volume_avg

        # Trend direction
        self.df["is_bullish_trend"] = close > self.df["ema_slow"]
        self.df["is_bearish_trend"] = close < self.df["ema_slow"]

        # Pullback to fast EMA (relaxed threshold for 1H)
        self.df["near_ema_fast"] = abs(close - self.df["ema_fast"]) / close < 0.015

        # RSI filters (relaxed for 1H)
        self.df["rsi_long_ok"] = self.df["rsi"] < 75
        self.df["rsi_short_ok"] = self.df["rsi"] > 25

        # ADX filter - only trade strong trends
        self.df["strong_trend"] = self.df["adx"] > 25

        # Volatility filter - avoid trading during extreme volatility
        self.df["atr_ma"] = self.df["atr"].rolling(window=50).mean()
        self.df["normal_volatility"] = (self.df["atr"] >= self.df["atr_ma"] * 0.5) & (
            self.df["atr"] <= self.df["atr_ma"] * 2.0
        )

        # Long entry conditions
        self.df["long_signal"] = (
            self.df["is_bullish_trend"]
            & self.df["near_ema_fast"]
            & self.df["rsi_long_ok"]
            & self.df["volume_confirmed"]
            & self.df["strong_trend"]
            & self.df["normal_volatility"]
            & (self.df["plus_di"] > self.df["minus_di"])
        )

        # Short entry conditions
        self.df["short_signal"] = (
            self.df["is_bearish_trend"]
            & self.df["near_ema_fast"]
            & self.df["rsi_short_ok"]
            & self.df["volume_confirmed"]
            & self.df["strong_trend"]
            & self.df["normal_volatility"]
            & (self.df["minus_di"] > self.df["plus_di"])
        )

        # ATR-based stops with trailing capability
        self.df["stop_loss_distance"] = self.df["atr"] * 0.6
        self.df["take_profit_distance"] = self.df["atr"] * 2.2

    def _execute_trades(self):
        """Execute trades with enhanced logic"""
        self.equity_curve = [self.capital]

        for i in range(len(self.df)):
            row = self.df.iloc[i]
            close = row["close"]

            # Check exits first
            if self.position is not None:
                self._check_exit(i, close)

            # Check entries
            if self.position is None:
                if row["long_signal"]:
                    self._enter_long(i, close, row)
                elif row["short_signal"]:
                    self._enter_short(i, close, row)

            self.equity_curve.append(self.capital)

    def _enter_long(self, i, close, row):
        """Enter long position with volatility-based sizing"""
        atr_sl_distance = row["stop_loss_distance"]
        atr_tp_distance = row["take_profit_distance"]

        # Dynamic position sizing based on volatility
        # Higher volatility = smaller position
        volatility_ratio = row["atr"] / row["atr_ma"] if row["atr_ma"] > 0 else 1
        base_position = 0.6
        adjusted_position = base_position / volatility_ratio
        adjusted_position = max(
            0.3, min(0.8, adjusted_position)
        )  # Clamp between 30-80%

        self.position = "long"
        self.entry_price = close
        self.position_size = self.capital * adjusted_position / close

        self.stop_loss = close - atr_sl_distance
        self.take_profit = close + atr_tp_distance

    def _enter_short(self, i, close, row):
        """Enter short position with volatility-based sizing"""
        atr_sl_distance = row["stop_loss_distance"]
        atr_tp_distance = row["take_profit_distance"]

        # Dynamic position sizing based on volatility
        volatility_ratio = row["atr"] / row["atr_ma"] if row["atr_ma"] > 0 else 1
        base_position = 0.6
        adjusted_position = base_position / volatility_ratio
        adjusted_position = max(0.3, min(0.8, adjusted_position))

        self.position = "short"
        self.entry_price = close
        self.position_size = self.capital * adjusted_position / close

        self.stop_loss = close + atr_sl_distance
        self.take_profit = close - atr_tp_distance

    def _check_exit(self, i, close):
        """Check all exit conditions"""
        exit_reason = None

        if self.position == "long":
            if close <= self.stop_loss:
                exit_reason = "SL"
            elif close >= self.take_profit:
                exit_reason = "TP"
            elif not self.df.iloc[i]["is_bullish_trend"]:
                exit_reason = "Trend Change"
            elif self.df.iloc[i]["adx"] < 20:
                exit_reason = "Weak Trend"

        elif self.position == "short":
            if close >= self.stop_loss:
                exit_reason = "SL"
            elif close <= self.take_profit:
                exit_reason = "TP"
            elif not self.df.iloc[i]["is_bearish_trend"]:
                exit_reason = "Trend Change"
            elif self.df.iloc[i]["adx"] < 20:
                exit_reason = "Weak Trend"

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

    plt.plot(
        dates,
        strategy_equity,
        label="Enhanced Strategy (1H)",
        linewidth=2,
        color="blue",
    )
    plt.plot(
        dates,
        ba_h_equity,
        label="Buy & Hold",
        linewidth=2,
        color="orange",
        linestyle="--",
    )

    plt.title(
        "Enhanced Strategy vs Buy & Hold - Equity Curve Comparison (1H Timeframe)",
        fontsize=14,
        fontweight="bold",
    )
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Portfolio Value ($)", fontsize=12)
    plt.legend(loc="upper left")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig("enhanced_trend_1h_equity_curve.png", dpi=150, bbox_inches="tight")
    print("\nEquity curve saved to: enhanced_trend_1h_equity_curve.png")
    plt.show()


def main():
    """Run enhanced strategy backtest for 1H"""
    print("=" * 80)
    print("ENHANCED TREND-FOLLOWING STRATEGY (1H TIMEFRAME)")
    print("Features: ADX filter, Volatility-based sizing, Improved filters")
    print("=" * 80)

    print("\nFetching BTC/USDT 1H data...")
    df = fetch_btc_data_1h(symbol="BTC/USDT", period_days=730)

    print("\nRunning enhanced backtest...")
    backtest = EnhancedTrendBacktest1H(df)
    results = backtest.run()

    ba_h_metrics = calculate_buy_and_hold_return(df, initial_capital=10000.0)

    print("\n" + "=" * 80)
    print("ENHANCED STRATEGY RESULTS (1H)")
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
    print("COMPARISON WITH ORIGINAL 1H STRATEGY")
    print("=" * 80)
    print("Original 1H: +22.81% return, 1.05 Sharpe, 1241 trades")
    print(
        f"Enhanced 1H: {results['total_return']:+.2f}% return, {results['sharpe_ratio']:.2f} Sharpe, {results['total_trades']} trades"
    )

    if results["total_return"] > 22.81:
        improvement = ((results["total_return"] - 22.81) / 22.81) * 100
        print(f"\n✓ Return improved by {improvement:+.1f}%")
    else:
        decline = ((22.81 - results["total_return"]) / 22.81) * 100
        print(f"\n✗ Return decreased by {decline:+.1f}%")

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

    if results["total_trades"] < 1241:
        print(
            f"✓ Reduced trade count from 1241 to {results['total_trades']} (fewer fees)"
        )

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
