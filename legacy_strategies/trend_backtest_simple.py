#!/usr/bin/env python3
"""
Simplified Trend-Following Strategy Backtest on BTC/USDT 4H
Optimizes parameters to beat Buy and Hold
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from btc_data_fetcher import fetch_btc_data_4h, calculate_buy_and_hold_return


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    multiplier = 2 / (period + 1)
    ema = prices.ewm(span=period, adjust=False).mean()
    return ema


def calculate_atr(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int
) -> pd.Series:
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()

    return atr


def calculate_rsi(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


class TrendFollowingBacktest:
    def __init__(self, df: pd.DataFrame, config: Dict):
        self.df = df.copy()
        self.config = config

        self.capital = 10000.0
        self.position_size = 0.0
        self.position = None
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.trades = []
        self.equity_curve = []

    def run(self) -> Dict:
        """Run backtest with given parameters"""
        self._calculate_indicators()
        self._generate_signals()
        self._execute_trades()
        self._calculate_metrics()

        return {
            "trades": self.trades,
            "equity_curve": self.equity_curve,
            "final_capital": self.capital,
            "total_return": (self.capital - 10000) / 10000 * 100,
            "num_trades": len(self.trades),
            "win_rate": sum(1 for t in self.trades if t["pnl"] > 0)
            / len(self.trades)
            * 100
            if self.trades
            else 0,
        }

    def _calculate_indicators(self):
        """Calculate all indicators"""
        close = self.df["close"]
        high = self.df["high"]
        low = self.df["low"]
        volume = self.df["volume"]

        ema_fast_period = self.config.get("ema_fast_period", 50)
        ema_slow_period = self.config.get("ema_slow_period", 200)
        atr_period = self.config.get("atr_period", 14)
        rsi_period = self.config.get("rsi_period", 14)
        volume_period = self.config.get("volume_period", 20)

        self.df["ema_fast"] = calculate_ema(close, ema_fast_period)
        self.df["ema_slow"] = calculate_ema(close, ema_slow_period)
        self.df["atr"] = calculate_atr(high, low, close, atr_period)
        self.df["rsi"] = calculate_rsi(close, rsi_period)
        self.df["volume_avg"] = volume.rolling(window=volume_period).mean()

    def _generate_signals(self):
        """Generate entry and exit signals"""
        close = self.df["close"]
        ema_fast = self.df["ema_fast"]
        ema_slow = self.df["ema_slow"]
        atr = self.df["atr"]
        rsi = self.df["rsi"]
        volume = self.df["volume"]
        volume_avg = self.df["volume_avg"]

        atr_multiplier_sl = self.config.get("atr_multiplier_sl", 0.5)
        atr_multiplier_tp = self.config.get("atr_multiplier_tp", 2.0)
        volume_multiplier = self.config.get("volume_multiplier", 1.2)
        rsi_overbought = self.config.get("rsi_overbought", 70)
        rsi_oversold = self.config.get("rsi_oversold", 30)
        pullback_threshold_pct = self.config.get("pullback_threshold_pct", 0.01)

        self.df["is_bullish_trend"] = close > ema_slow
        self.df["is_bearish_trend"] = close < ema_slow

        self.df["near_ema_fast"] = (
            abs(close - ema_fast) / close < pullback_threshold_pct
        )

        self.df["volume_confirmed"] = volume >= volume_avg * volume_multiplier

        self.df["rsi_long_ok"] = rsi < rsi_overbought
        self.df["rsi_short_ok"] = rsi > rsi_oversold

        self.df["atr_sl_distance"] = atr * atr_multiplier_sl
        self.df["atr_tp_distance"] = atr * atr_multiplier_tp

        self.df["long_signal"] = (
            self.df["is_bullish_trend"]
            & self.df["near_ema_fast"]
            & self.df["volume_confirmed"]
            & self.df["rsi_long_ok"]
        )

        self.df["short_signal"] = (
            self.df["is_bearish_trend"]
            & self.df["near_ema_fast"]
            & self.df["volume_confirmed"]
            & self.df["rsi_short_ok"]
        )

    def _execute_trades(self):
        """Execute trades based on signals"""
        self.equity_curve = [self.capital]

        for i in range(len(self.df)):
            row = self.df.iloc[i]
            close = row["close"]

            if self.position is not None:
                self._check_exit(i, close)

            if self.position is None and (row["long_signal"] or row["short_signal"]):
                self._enter_position(i, row)

            self.equity_curve.append(self.capital)

    def _enter_position(self, i: int, row: pd.Series):
        """Enter a position"""
        close = row["close"]
        atr_sl_distance = row["atr_sl_distance"]
        atr_tp_distance = row["atr_tp_distance"]

        position_size_pct = self.config.get("position_size_pct", 0.5)
        self.position_size = self.capital * position_size_pct / close

        if row["long_signal"]:
            self.position = "long"
            self.entry_price = close
            self.stop_loss = close - atr_sl_distance
            self.take_profit = close + atr_tp_distance
        else:
            self.position = "short"
            self.entry_price = close
            self.stop_loss = close + atr_sl_distance
            self.take_profit = close - atr_tp_distance

    def _check_exit(self, i: int, close: float):
        """Check if we should exit position"""
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

    def _close_position(self, i: int, close: float, reason: str):
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
        self.stop_loss = None
        self.take_profit = None
        self.position_size = 0.0

    def _calculate_metrics(self):
        """Calculate performance metrics"""
        if not self.trades:
            return

        returns = np.diff(self.equity_curve) / np.array(self.equity_curve[:-1])

        if len(returns) > 1:
            sharpe = (
                (returns.mean() / returns.std()) * (len(returns) ** 0.5)
                if returns.std() != 0
                else 0
            )
        else:
            sharpe = 0

        equity_array = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max * 100
        max_drawdown = drawdown.min()

        self.metrics = {
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "total_trades": len(self.trades),
            "win_rate": sum(1 for t in self.trades if t["pnl"] > 0)
            / len(self.trades)
            * 100,
            "total_return": (self.capital - 10000) / 10000 * 100,
        }


def run_single_backtest(config: Dict, df: pd.DataFrame) -> Dict:
    """Run single backtest with given config"""
    backtest = TrendFollowingBacktest(df, config)
    results = backtest.run()

    results.update(backtest.metrics)
    results["config"] = config

    return results


def grid_search(df: pd.DataFrame) -> Tuple[Dict, Dict]:
    """Perform grid search for optimal parameters"""
    print("\n" + "=" * 80)
    print("GRID SEARCH FOR TREND FOLLOWING STRATEGY")
    print("=" * 80)

    param_grid = {
        "ema_fast_period": [34, 50, 55],
        "ema_slow_period": [144, 200, 252],
        "atr_period": [14, 20],
        "atr_multiplier_sl": [0.4, 0.5, 0.6],
        "atr_multiplier_tp": [1.5, 2.0, 2.5],
        "rsi_period": [10, 14, 21],
        "volume_multiplier": [1.0, 1.2, 1.5],
        "position_size_pct": [0.3, 0.5, 0.7],
    }

    best_result = None
    best_config = None
    iteration = 0

    total_iterations = (
        len(param_grid["ema_fast_period"])
        * len(param_grid["ema_slow_period"])
        * len(param_grid["atr_period"])
        * len(param_grid["atr_multiplier_sl"])
        * len(param_grid["atr_multiplier_tp"])
        * len(param_grid["rsi_period"])
        * len(param_grid["volume_multiplier"])
        * len(param_grid["position_size_pct"])
    )

    print(f"Total iterations: {total_iterations}")
    print("This will take a while...\n")

    for ema_fast in param_grid["ema_fast_period"]:
        for ema_slow in param_grid["ema_slow_period"]:
            if ema_fast >= ema_slow:
                continue

            for atr_p in param_grid["atr_period"]:
                for atr_sl in param_grid["atr_multiplier_sl"]:
                    for atr_tp in param_grid["atr_multiplier_tp"]:
                        for rsi_p in param_grid["rsi_period"]:
                            for vol_mult in param_grid["volume_multiplier"]:
                                for pos_size in param_grid["position_size_pct"]:
                                    iteration += 1

                                    config = {
                                        "ema_fast_period": ema_fast,
                                        "ema_slow_period": ema_slow,
                                        "atr_period": atr_p,
                                        "atr_multiplier_sl": atr_sl,
                                        "atr_multiplier_tp": atr_tp,
                                        "rsi_period": rsi_p,
                                        "volume_multiplier": vol_mult,
                                        "position_size_pct": pos_size,
                                    }

                                    print(
                                        f"Iteration {iteration}/{total_iterations}: "
                                        f"EMA({ema_fast},{ema_slow}) ATR({atr_p}) "
                                        f"SL({atr_sl}) TP({atr_tp}) RSI({rsi_p}) "
                                        f"Vol({vol_mult}) Size({pos_size * 100:.0f}%)"
                                    )

                                    try:
                                        result = run_single_backtest(config, df)

                                        print(
                                            f"  Result: {result['total_return']:+.2f}% "
                                            f"| Win Rate: {result['win_rate']:.1f}% "
                                            f"| Sharpe: {result['sharpe_ratio']:.2f} "
                                            f"| Trades: {result['total_trades']}"
                                        )

                                        if (
                                            best_result is None
                                            or result["total_return"]
                                            > best_result["total_return"]
                                        ):
                                            best_result = result
                                            best_config = config
                                            print(f"  *** NEW BEST ***")

                                    except Exception as e:
                                        print(f"  Error: {e}")
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
        print(
            f"Difference: {best_result['total_return'] - ba_h_metrics['total_return_pct']:+.2f}%"
        )
        print("=" * 80)

        if best_result["total_return"] >= ba_h_metrics["total_return_pct"] * 0.9:
            print("\n✓ Strategy beats or is within 90% of Buy and Hold!")
        else:
            print("\n✗ Strategy needs more optimization")

    else:
        default_config = {
            "ema_fast_period": 50,
            "ema_slow_period": 200,
            "atr_period": 14,
            "atr_multiplier_sl": 0.5,
            "atr_multiplier_tp": 2.0,
            "rsi_period": 14,
            "volume_multiplier": 1.2,
            "position_size_pct": 0.5,
        }

        print(f"\nRunning default configuration...")
        result = run_single_backtest(default_config, df)

        print("\n" + "=" * 80)
        print("BACKTEST RESULTS")
        print("=" * 80)
        print(f"Total Return: {result['total_return']:+.2f}%")
        print(f"Buy & Hold Return: {ba_h_metrics['total_return_pct']:+.2f}%")
        print(
            f"Difference: {result['total_return'] - ba_h_metrics['total_return_pct']:+.2f}%"
        )
        print(f"Win Rate: {result['win_rate']:.1f}%")
        print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {result['max_drawdown']:.2f}%")
        print(f"Total Trades: {result['total_trades']}")
        print("=" * 80)
