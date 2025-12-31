#!/usr/bin/env python3
"""Simple dashboard for Smooth Trend 4H strategy"""

from src.data.fetcher import DataFetcher
from src.strategies.smooth_trend_4h import SmoothTrend4HStrategy
from src.backtest.engine import BacktestEngine
from src.analytics import Analytics


def main():
    timeframe = "4h"
    period_days = 365 * 5

    fetcher = DataFetcher(exchange="binance")
    df = fetcher.fetch("BTC/USDT", timeframe, period_days=period_days)

    date_start = str(df.index[0])[:10]
    date_end = str(df.index[-1])[:10]

    config = {
        "ema_fast": 76,
        "ema_slow": 99,
        "atr_period": 14,
        "atr_multiplier_sl": 0.4,
        "atr_multiplier_tp": 3.38,
        "trail_multiplier": 0.77,
        "rsi_period": 12,
        "rsi_long_min": 26,
        "rsi_long_max": 54,
        "rsi_short_min": 32,
        "rsi_short_max": 48,
        "adx_period": 14,
        "adx_threshold": 26,
        "volume_period": 20,
        "volume_multiplier": 0.9,
        "pullback_threshold_pct": 0.0146,
        "time_stop_bars": 15,
        "position_size_pct": 0.62,
        "initial_capital": 10000.0,
        "name": "Smooth Trend 4H",
        "timeframe": timeframe,
        "date_range": f"{date_start} to {date_end}",
    }

    strategy = SmoothTrend4HStrategy(config)
    engine = BacktestEngine({"initial_capital": 10000.0})
    results = engine.run(df, strategy)

    buy_hold = fetcher.calculate_buy_and_hold(df)

    analytics = Analytics(
        results, df=df, name="Smooth Trend 4H", config=config, buy_hold_results=buy_hold
    )

    analytics.print_summary()
    analytics.save_json(str(analytics.output_dir / "report.json"))
    analytics.save_csv(str(analytics.output_dir / "metrics.csv"))
    dashboard_path = analytics.generate_dashboard("dashboard.html")

    print(f"\nDashboard: {dashboard_path}")


if __name__ == "__main__":
    main()
