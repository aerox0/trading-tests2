#!/usr/bin/env python3
"""
Pure Trend-Following Strategy Backtest on BTC/USDT 4H
Uses EMA crossover for trend following
"""

import pandas as pd
import numpy as np
from typing import Dict
from btc_data_fetcher import fetch_btc_data_4h, calculate_buy_and_hold_return


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return prices.ewm(span=period, adjust=False).mean()


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=class="number">period</class>).mean()


class PureTrendFollowingBacktest:
    def __init__(self, df: pd.DataFrame, config: Dict):
        self.df = df.copy()
        self.config = config

        self.capital = 10000.0
        self.position = None
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.trades = []
        self.equity_curve = []

    def run(self) -> Dict:
        """Run backtest"""
        self._calculate_indicators()
        self._generate_signals()
        self._execute_trades()
        return self._calculate_metrics()

    def _calculate_indicators(self):
        """Calculate all indicators"""
        close = self.df["close"]
        high = self.df["high"]
        low = self.df["low"]

        ema_fast_period = self.config.get("ema_fast_period", 50)
        ema_slow_period = self.config.get("ema_slow_period", 200)
        atr_period = self.config.get("atr_period", 14)

        self.df["ema_fast"] = calculate_ema(close, ema_fast_period)
        self.df["ema_slow"] = calculate_ema(close, ema_slow_period)
        self.df["atr"] = calculate_atr(high, low, close, atr_period)

    def _generate_signals(self):
        """Generate signals based on EMA crossover"""
        close = self.df["close"]
        ema_fast = self.df["ema_fast"]
        ema_slow = self.df["ema_slow"]

        atr_sl = self.config.get("atr_multiplier_sl", 1.0)
        atr_tp = self.config.get("atr_multiplier_tp", 2.0)

        self.df["bullish_crossover"] = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))
        self.df["bearish_crossover"] = (ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1))

        self.df["bullish_trend"] = ema_fast > ema_slow
        self.df["bearish_trend"] = ema_fast < ema_slow

        self.df["stop_loss_distance"] = self.df["atr"] * atr_sl
        self.df["take_profit_distance"] = self.df["atr"] * atr_tp

    def _execute_trades(self):
        """Execute trades"""
        self.equity_curve = [self.capital]

        for i in range(len(self.df)):
            row = self.df.iloc[i]
            close = row["close"]

            if self.position is not None:
                self._check_exit(i, close)

            if self.position is None:
                if row["bullish_crossover"]:
                    self._enter_long(i, row)
                elif row["bearish_crossover"]:
                    self._enter_short(i, row)

            self.equity_curve.append(self.capital)

    def _enter_long(self, i: int, row: pd.Series):
        """Enter long position"""
        position_size_pct = self.config.get("position_size_pct", 1.0)
        self.position_size = self.capital * position_size_pct / row["close"]

        self.position = "long"
        self.entry_price = row["close"]
        self.stop_loss = row["close"] - row["stop_loss_distance"]
        self.take_profit = row["close"] + row["take_profit_distance"]

    def _enter_short(self, i: int, row: pd.Series):
        """Enter short position"""
        position_size_pct = self.config.get("position_size_pct", 1.0)
        self.position_size = self.capital * position_size_pct / row["close"]

        self.position = "short"
        self.entry_price = row["close"]
        self.stop_loss = row["close"] + row["stop_loss_distance"]
        self.take_profit = row["close"] - row["take_profit_distance"]

    def _check_exit(self, i: int, close: float):
        """Check exit conditions"""
        exit_reason = None

        if self.position == "long":
            if close <= self.stop_loss:
                exit_reason = "SL"
            elif close >= self.take_profit:
                exit_reason = "TP"
            elif not self.df.iloc[i]["bullish_trend"]:
                exit_reason = "Trend Reversal"

        elif self.position == "short":
            if close >= self.stop_loss:
                exit_reason = "SL"
            elif close <= self.take_profit:
                exit_reason = "TP"
            elif not self.df.iloc[i]["bearish_trend"]:
                exit_reason = "Trend Reversal"

        if exit_reason:
            self._close_position(i, close, exit_reason)

    def _close_position(self, i: int, close: float, reason: str):
        """Close position"""
        if self.position == "long":
            pnl = (close - self.entry_price) * self.position_size
        else:
            pnl = (self.entry_price - close) * self.position_size

        self.capital += pnl
        self.trades.append({
            "entry": self.entry_price,
            "exit": close,
            "pnl": pnl,
            "reason": reason,
            "type": self.position,
            "bar_index": i,
        })

        self.position = None
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None

    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
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
            "win_rate": sum(1 for t in self.trades if t["pnl"] > 0) / len(self.trades) * 100 if self.trades else 0,
            "final_capital": self.capital,
        }


def run_backtest(config: Dict, df: pd.DataFrame) -> Dict:
    """Run backtest with given config"""
    backtest = PureTrendFollowingBacktest(df, config)
    results = backtest.run()
    results["config"] = config
    return results


def grid_search(df: pd.DataFrame) -> tuple[Dict, Dict]:
    """Grid search for optimal parameters"""
    print("\n" + "=" * 80)
    print("GRID SEARCH FOR PURE TREND FOLLOWING STRATEGY")
    print("=" * 80)

    param_grid = {
        "ema_fast_period": [20, 34, 50],
        "ema_slow_period": [100, 144, 200],
        "atr_period": [7, 14, 21],
        "atr_multiplier_sl": [0.8, 1.0, 1.5],
        "atr_multiplier_tp": [1.5, 2.0, 3.0],
        "position_size_pct": [0.5, 0.75, 1.0],
    }

    best_result = None
    best_config = None
    iteration = 0

    total_iterations = (
        len(param_grid["ema_fast_period"]) *
        len(param_grid["ema_slow_period"]) *
        len(param_grid["atr_period"]) *
        len(param_grid["atr_multiplier_sl"]) *
        len(param_grid["atr_multiplier_tp"]) *
        len(param_grid["position_size_pct"])
    )

    print(f"Total iterations: {total_iterations}")

    for ema_fast in param_grid["ema_fast_period"]:
        for ema_slow in param_grid["ema_slow_period"]:
            if ema_fast >= ema_slow:
                continue

            for atr_p in param_grid["atr_period"]:
                for atr_sl in param_grid["atr_multiplier_sl"]:
                    for atr_tp in param_grid["atr_multiplier_tp"]:
                        for pos_size in param_grid["position_size_pct"]:
                            iteration += 1

                            config = {
                                "ema_fast_period": ema_fast,
                                "ema_slow_period": ema_slow,
                                "atr_period": atr_p,
                                "atr_multiplier_sl": atr_sl,
                                "atr_multiplier_tp": atr_tp,
                                "position_size_pct": pos_size,
                            }

                            if iteration % 50 == 0:
                                print(f"Iteration {iteration}/{total_iterations}: "
                                      f"EMA({ema_fast},{ema_slow}) ATR({atr_p}) SL({atr_sl}) TP({atr_tp})")

                            try:
                                result = run_backtest(config, df)

                                if best_result is None or result["total_return"] > best_result["total_return"]:
                                    best_result = result
                                    best_config = config
                                    print(f"  *** NEW BEST: {result['total_return']:+.2f}% ***")

                            except Exception as e:
                                continue

    print("\n" + "=" * 80)
    print("GRID SEARCH COMPLETE")
    print("=" * 80)
    print("\nBest Parameters:")
    for k, v in best_config.items():
        print(f"  {k}: {v}")

    print(f"\nBest Result:")
    print(f"  Total Return: {best_result['total_return']:+.2f}%")
    print(f"  Win Rate: {best_result['win_rate']:.1f}%")
    print(f"  Sharpe Ratio: {best_result['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {best_result['max_drawdown']:.2f}%")
    print(f"  Total Trades: {best_result['total_trades']}")
    print("=" * 80)

    return best_result, best_config


if __name__ == "__main__":
    import sys

    print("Fetching BTC/USDT 4H data...")
    df = fetch_btc_data_4h(symbol="BTC/USDT", period_days=730)

    print("\nCalculating Buy and Hold baseline...")
    ba_h_metrics = calculate_buy_and_hold_return(df, initial_capital=10000.0)

    if len(sys.argv) > 1 and sys.argv[1] == "grid":
        best_result, best_config = grid_search(df)

        print("\n" + "=" * 80)
        print("COMPARISON WITH BUY AND HOLD")
        print("=" * 80)
        print(f"Strategy Return: {best_result['total_return']:+.2f}%")
        print(f"Buy & Hold Return: {ba_h_metrics['total_return_pct']:+.2f}%")
        print(f"Difference: {best_result['total_return'] - ba_h_metrics['total_return_pct']:+.2f}%")
        print("=" * 80)

        if best_result['total_return'] >= ba_h_metrics['total_return_pct'] * 0.9:
            print("\n✓ Strategy beats or is within 90% of Buy and Hold!")
        else:
            print("\n✗ Strategy needs more optimization")
    else:
        default_config = {
            "ema_fast_period": 34,
            "ema_slow_period": 144,
            "atr_period": 14,
            "atr_multiplier_sl": 1.0,
            "atr_multiplier_tp": 2.0,
            "position_size_pct": 0.75,
        }

        print(f"\nRunning default configuration...")
        result = run_backtest(default_config, df)

        print("\n" + "=" * 80)
        print("BACKTEST RESULTS")
        print("=" * 80)
        print(f"Total Return: {result['total_return']:+.2f}%")
        print(f"Buy & Hold Return: {ba_h_metrics['total_return_pct']:+.2f}%")
        print(f"Difference: {result['total_return'] - ba_h_metrics['total_return_pct']:+.2f}%")
        print(f"Win Rate: {result['win_rate']:.1f}%")
        print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {result['max_drawdown']:.2f}%")
        print(f"Total Trades: {result['total_trades']}")
        print("=" * 80)
