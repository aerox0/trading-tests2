#!/usr/bin/env python3
"""
Simple example demonstrating the trading framework
Run backtest with trend-following strategy on BTC/USDT
"""

import sys

sys.path.insert(0, "/Users/aerox0/dev/trading-tests2")

from src.data.fetcher import DataFetcher
from src.strategies.trend_following import TrendFollowingStrategy
from src.backtest.engine import BacktestEngine
import pandas as pd


def main():
    """Run example backtest"""
    print("=" * 80)
    print("TRADING FRAMEWORK EXAMPLE")
    print("=" * 80)

    # Step 1: Fetch data
    print("\nStep 1: Fetching data...")
    timeframe = "4h"
    period_days = 365
    fetcher = DataFetcher(exchange="binance")
    df = fetcher.fetch(symbol="BTC/USDT", timeframe=timeframe, period_days=period_days)

    date_start = str(df.index[0])[:10]
    date_end = str(df.index[-1])[:10]

    # Step 2: Configure strategy
    print("\nStep 2: Configuring strategy...")
    config = {
        "ema_fast": 55,
        "ema_slow": 144,
        "atr_period": 14,
        "atr_multiplier_sl": 0.6,
        "atr_multiplier_tp": 2.0,
        "rsi_period": 14,
        "volume_period": 20,
        "volume_multiplier": 1.0,
        "pullback_threshold_pct": 0.01,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "position_size_pct": 0.7,
        "initial_capital": 10000.0,
        "name": "Trend Following Example",
        "timeframe": timeframe,
        "date_range": f"{date_start} to {date_end}",
    }
    print(
        f"  Config: EMA({config['ema_fast']},{config['ema_slow']}) "
        f"SL {config['atr_multiplier_sl']}x TP {config['atr_multiplier_tp']}x"
    )

    # Step 3: Create strategy
    print("\nStep 3: Creating strategy...")
    strategy = TrendFollowingStrategy(config)
    print(f"  Strategy: {strategy.name}")

    # Step 4: Configure backtest engine
    print("\nStep 4: Configuring backtest engine...")
    engine_config = {"initial_capital": 10000.0}
    engine = BacktestEngine(engine_config)

    # Step 5: Run backtest
    print("\nStep 5: Running backtest...")
    results = engine.run(df, strategy)

    # Step 6: Display results
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    print(f"Total Return: {results['total_return']:+.2f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']:.1f}%")
    print(f"Final Capital: ${results['final_capital']:,.2f}")

    # Calculate Buy & Hold baseline
    ba_h = fetcher.calculate_buy_and_hold(df)
    print(f"\n" + "-" * 80)
    print("BUY & HOLD BASELINE")
    print("-" * 80)
    print(f"Return: {ba_h['total_return_pct']:+.2f}%")
    print(f"Sharpe: {ba_h['sharpe_ratio']:.2f}")
    print(f"Drawdown: {ba_h['max_drawdown_pct']:.2f}%")

    print(f"\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print(f"Strategy Return: {results['total_return']:+.2f}%")
    print(f"Buy & Hold Return: {ba_h['total_return_pct']:+.2f}%")
    print(f"Difference: {results['total_return'] - ba_h['total_return_pct']:+.2f}%")
    print("=" * 80)

    return results


if __name__ == "__main__":
    results = main()
