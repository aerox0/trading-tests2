#!/usr/bin/env python3
"""
Test all new plotting functions
"""

import sys

sys.path.insert(0, "/Users/aerox0/dev/trading-tests2")

from src.data.fetcher import DataFetcher
from src.strategies.trend_following import TrendFollowingStrategy
from src.backtest.engine import BacktestEngine
from src.analytics import Analytics


def main():
    """Test all new plotting functions"""
    print("=" * 80)
    print("TESTING NEW PLOTTING FUNCTIONS")
    print("=" * 80)

    # Run backtest
    fetcher = DataFetcher(exchange="binance")
    df = fetcher.fetch("BTC/USDT", "4h", period_days=365)

    config = {
        "ema_fast": 55,
        "ema_slow": 144,
        "atr_period": 14,
        "atr_multiplier_sl": 0.6,
        "atr_multiplier_tp": 2.0,
        "rsi_period": 14,
        "position_size_pct": 0.7,
        "initial_capital": 10000.0,
    }

    strategy = TrendFollowingStrategy(config)
    engine = BacktestEngine({"initial_capital": 10000.0})
    results = engine.run(df, strategy)

    # Calculate buy & hold
    buy_hold = fetcher.calculate_buy_and_hold(df)

    # Create analytics object
    analytics = Analytics(
        results,
        df=df,
        name="Trend Following Strategy",
        config=config,
        buy_hold_results=buy_hold,
    )

    # Check if trades have timestamps
    print(
        f"\nTrades with entry_time: {sum(1 for t in results['trades'] if 'entry_time' in t and t['entry_time'] is not None)}/{len(results['trades'])}"
    )
    print(
        f"Trades with exit_time: {sum(1 for t in results['trades'] if 'exit_time' in t and t['exit_time'] is not None)}/{len(results['trades'])}"
    )

    if results["trades"] and "entry_time" in results["trades"][0]:
        print(f"Sample trade: {results['trades'][0]}")

    # Generate all plots
    print("\nGenerating all enhanced plots...")
    analytics.plot_all()

    print(f"\n" + "=" * 80)
    print(f"All plots saved to: {analytics.output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
