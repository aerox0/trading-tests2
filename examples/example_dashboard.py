#!/usr/bin/env python3
"""
Example: Dashboard Generation
Demonstrates how to generate a single dashboard with all embedded charts
"""

import sys

sys.path.insert(0, "/Users/aerox0/dev/trading-tests2")

from src.data.fetcher import DataFetcher
from src.strategies.trend_following import TrendFollowingStrategy
from src.backtest.engine import BacktestEngine
from src.analytics import Analytics


def main():
    """Generate dashboard with all embedded charts"""
    print("=" * 80)
    print("DASHBOARD GENERATION EXAMPLE")
    print("=" * 80)

    # Run backtest
    timeframe = "4h"
    period_days = 365
    fetcher = DataFetcher(exchange="binance")
    df = fetcher.fetch("BTC/USDT", timeframe, period_days=period_days)

    date_start = str(df.index[0])[:10]
    date_end = str(df.index[-1])[:10]

    config = {
        "ema_fast": 55,
        "ema_slow": 144,
        "atr_period": 14,
        "atr_multiplier_sl": 0.6,
        "atr_multiplier_tp": 2.0,
        "rsi_period": 14,
        "position_size_pct": 0.7,
        "initial_capital": 10000.0,
        "timeframe": timeframe,
        "date_range": f"{date_start} to {date_end}",
    }

    strategy = TrendFollowingStrategy(config)
    engine = BacktestEngine({"initial_capital": 10000.0})
    results = engine.run(df, strategy)

    # Calculate buy & hold
    buy_hold = fetcher.calculate_buy_and_hold(df)

    # Create analytics object (auto-creates timestamped output directory)
    analytics = Analytics(
        results,
        df=df,
        name="Trend Following Strategy",
        config=config,
        buy_hold_results=buy_hold,
    )

    # Print summary
    analytics.print_summary()

    # Generate single HTML dashboard with all embedded charts
    # This creates a self-contained HTML file with:
    # - Performance metrics
    # - Strategy configuration
    # - Interactive tabs with charts:
    #   - Equity Curve
    #   - Drawdown
    #   - Monthly Returns
    #   - PnL Distribution
    print("\nGenerating dashboard...")
    dashboard_path = analytics.generate_dashboard("dashboard.html")

    # Optionally, generate individual files too
    print("\nGenerating individual files...")
    analytics.save_csv(str(analytics.output_dir / "metrics.csv"))
    analytics.save_json(str(analytics.output_dir / "report.json"))

    print(f"\n" + "=" * 80)
    print(f"Dashboard saved to: {dashboard_path}")
    print(f"All outputs saved to: {analytics.output_dir}")
    print("\nOpen the dashboard in your browser to see interactive charts!")
    print("=" * 80)


if __name__ == "__main__":
    main()
