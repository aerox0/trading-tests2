#!/usr/bin/env python3
"""
Hybrid Strategy: Combines Buy and Hold with Active Trend Following
50% passive (Buy & Hold) + 50% active (Optimized Trend Following)
This balances the strong uptrend benefit with potential alpha from active trading
"""

import pandas as pd
import numpy as np
from btc_data_fetcher import fetch_btc_data_4h, calculate_buy_and_hold_return


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


class HybridBacktest:
    """
    Hybrid strategy: 50% Buy & Hold + 50% Active Trend Following
    """

    def __init__(self, df, passive_allocation=0.5):
        self.df = df.copy()
        self.passive_allocation = passive_allocation  # % of capital for buy & hold
        self.active_allocation = 1.0 - passive_allocation  # % for active trading

        self.passive_capital = 10000.0 * passive_allocation
        self.active_capital = 10000.0 * self.active_allocation

        # Passive: Buy and hold BTC
        self.passive_btc_amount = self.passive_capital / df["close"].iloc[0]

        # Active: Trend following with optimized parameters
        self.active_position = None
        self.active_entry_price = None
        self.active_position_size = 0.0
        self.active_trades = []

        # Tracking
        self.equity_curve = []

    def run(self):
        """Run hybrid backtest"""
        self._calculate_indicators()
        self._execute_trades()
        return self._calculate_metrics()

    def _calculate_indicators(self):
        """Calculate indicators for active strategy"""
        close = self.df["close"]
        high = self.df["high"]
        low = self.df["low"]

        # Optimized parameters from grid search
        self.df["ema_fast"] = calculate_ema(close, 55)
        self.df["ema_slow"] = calculate_ema(close, 144)
        self.df["atr"] = calculate_atr(high, low, close, 14)

        self.df["is_bullish_trend"] = close > self.df["ema_slow"]
        self.df["near_ema_fast"] = abs(close - self.df["ema_fast"]) / close < 0.01
        self.df["stop_loss_distance"] = self.df["atr"] * 0.6
        self.df["take_profit_distance"] = self.df["atr"] * 2.5

    def _execute_trades(self):
        """Execute hybrid strategy"""
        for i in range(len(self.df)):
            close = self.df["close"].iloc[i]

            # Calculate passive value
            passive_value = self.passive_btc_amount * close / self.df["close"].iloc[0]

            # Manage active position
            if self.active_position is not None:
                self._check_active_exit(i, close)

            if self.active_position is None:
                self._check_active_entry(i)

            # Total equity
            active_value = self.active_capital
            total_equity = passive_value + active_value

            # Adjust active capital based on PnL
            if self.active_position is None:
                pnl = self.active_capital - 10000.0 * self.active_allocation
                self.active_capital = 10000.0 * self.active_allocation + pnl

            self.equity_curve.append(total_equity)

    def _check_active_entry(self, i):
        """Check if we should enter active trade"""
        row = self.df.iloc[i]

        if row["is_bullish_trend"] and row["near_ema_fast"]:
            self.active_position = "long"
            self.active_entry_price = row["close"]
            self.active_position_size = self.active_capital / row["close"]
        elif not row["is_bullish_trend"] and row["near_ema_fast"]:
            self.active_position = "short"
            self.active_entry_price = row["close"]
            self.active_position_size = self.active_capital / row["close"]

    def _check_active_exit(self, i, close):
        """Check if we should exit active trade"""
        stop_loss = self.active_entry_price - self.df.iloc[i]["stop_loss_distance"]
        take_profit = self.active_entry_price + self.df.iloc[i]["take_profit_distance"]
        is_bullish = self.df.iloc[i]["is_bullish_trend"]

        exit_reason = None

        if self.active_position == "long":
            if close <= stop_loss:
                exit_reason = "SL"
            elif close >= take_profit:
                exit_reason = "TP"
            elif not is_bullish:
                exit_reason = "Trend Change"

        elif self.active_position == "short":
            if close >= stop_loss:
                exit_reason = "SL"
            elif close <= take_profit:
                exit_reason = "TP"
            elif is_bullish:
                exit_reason = "Trend Change"

        if exit_reason:
            if self.active_position == "long":
                pnl = (close - self.active_entry_price) * self.active_position_size
            else:
                pnl = (self.active_entry_price - close) * self.active_position_size

            self.active_capital += pnl
            self.active_trades.append(
                {
                    "entry": self.active_entry_price,
                    "exit": close,
                    "pnl": pnl,
                    "reason": exit_reason,
                    "type": self.active_position,
                    "bar_index": i,
                }
            )

            self.active_position = None
            self.active_entry_price = None
            self.active_position_size = 0.0

    def _calculate_metrics(self):
        """Calculate performance metrics"""
        final_equity = self.equity_curve[-1]
        total_return = (final_equity - 10000.0) / 10000.0 * 100

        returns = np.diff(self.equity_curve) / np.array(self.equity_curve[:-1])

        if len(returns) > 1 and returns.std() != 0:
            sharpe = (returns.mean() / returns.std()) * (len(returns) ** 0.5)
        else:
            sharpe = 0

        equity_array = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max * 100
        max_drawdown = drawdown.min()

        # Calculate active strategy metrics
        active_wins = [t for t in self.active_trades if t["pnl"] > 0]
        win_rate = (
            len(active_wins) / len(self.active_trades) * 100
            if self.active_trades
            else 0
        )

        return {
            "total_return": total_return,
            "final_equity": final_equity,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "active_trades": len(self.active_trades),
            "active_win_rate": win_rate,
            "active_pnl": sum(t["pnl"] for t in self.active_trades),
        }


def main():
    """Run hybrid strategy backtest"""
    print("=" * 80)
    print("HYBRID STRATEGY: 50% BUY & HOLD + 50% ACTIVE TREND")
    print("=" * 80)

    print("\nFetching BTC/USDT 4H data...")
    df = fetch_btc_data_4h(symbol="BTC/USDT", period_days=730)

    ba_h_metrics = calculate_buy_and_hold_return(df, initial_capital=10000.0)

    # Test different allocations
    allocations = [0.3, 0.5, 0.7]

    best_result = None
    best_allocation = None

    for allocation in allocations:
        print(f"\nTesting {allocation * 100:.0f}% passive allocation...")
        backtest = HybridBacktest(df, passive_allocation=allocation)
        results = backtest.run()

        print(f"  Total Return: {results['total_return']:+.2f}%")
        print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {results['max_drawdown']:.2f}%")
        print(f"  Active Trades: {results['active_trades']}")
        print(f"  Active Win Rate: {results['active_win_rate']:.1f}%")

        if best_result is None or results["total_return"] > best_result["total_return"]:
            best_result = results
            best_allocation = allocation
            print(f"  *** NEW BEST ***")

    print("\n" + "=" * 80)
    print("HYBRID STRATEGY - BEST RESULT")
    print("=" * 80)
    print(
        f"Optimal Allocation: {best_allocation * 100:.0f}% Passive / {100 - best_allocation * 100:.0f}% Active"
    )
    print(f"\nPerformance Metrics:")
    print(f"  Total Return: {best_result['total_return']:+.2f}%")
    print(f"  Buy & Hold Return: {ba_h_metrics['total_return_pct']:+.2f}%")
    print(
        f"  Difference: {best_result['total_return'] - ba_h_metrics['total_return_pct']:+.2f}%"
    )
    print(
        f"  Sharpe Ratio: {best_result['sharpe_ratio']:.2f} vs {ba_h_metrics['sharpe_ratio']:.2f} (BaH)"
    )
    print(
        f"  Max Drawdown: {best_result['max_drawdown']:.2f}% vs {ba_h_metrics['max_drawdown_pct']:.2f}% (BaH)"
    )
    print(f"  Active Trades: {best_result['active_trades']}")
    print(f"  Active Win Rate: {best_result['active_win_rate']:.1f}%")

    print("\n" + "=" * 80)
    print("ASSESSMENT")
    print("=" * 80)

    if best_result["total_return"] >= ba_h_metrics["total_return_pct"] * 0.95:
        print("✓ Hybrid strategy beats or is within 95% of Buy and Hold!")
    elif best_result["total_return"] >= ba_h_metrics["total_return_pct"] * 0.9:
        print("✓ Hybrid strategy is within 90% of Buy and Hold")
    elif best_result["total_return"] >= ba_h_metrics["total_return_pct"] * 0.8:
        print("✓ Hybrid strategy is within 80% of Buy and Hold")
    else:
        print("✗ Hybrid strategy underperforms Buy and Hold")

    if best_result["sharpe_ratio"] > ba_h_metrics["sharpe_ratio"] * 1.3:
        print("✓ Significantly better risk-adjusted returns (Sharpe)")
    elif best_result["sharpe_ratio"] > ba_h_metrics["sharpe_ratio"]:
        print("✓ Better risk-adjusted returns (Sharpe)")
    else:
        print("✗ Lower risk-adjusted returns than Buy and Hold")

    if best_result["max_drawdown"] < ba_h_metrics["max_drawdown_pct"]:
        print("✓ Better drawdown control than Buy and Hold")
    else:
        print("✗ Worse drawdown than Buy and Hold")

    print("=" * 80)

    return best_result


if __name__ == "__main__":
    main()
