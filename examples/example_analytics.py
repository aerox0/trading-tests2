#!/usr/bin/env python3
"""
Example: Using Analytics Module
Demonstrates all analytics features
"""

import sys

sys.path.insert(0, "/Users/aerox0/dev/trading-tests2")

from src.data.fetcher import DataFetcher
from src.strategies.trend_following import TrendFollowingStrategy
from src.backtest.engine import BacktestEngine
from src.analytics import (
    Analytics,
    compare_strategies,
    rank_strategies,
    generate_comparison_reports,
)


def example_1_basic_analytics():
    """Example 1: Basic analytics - dashboard with all charts"""
    print("=" * 80)
    print("EXAMPLE 1: Basic Analytics Dashboard")
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
        name="Trend Following (EMA 55/144)",
        config=config,
        buy_hold_results=buy_hold,
    )

    # Print formatted summary (no more print statements!)
    analytics.print_summary()

    # Generate single HTML dashboard with all embedded charts
    print("\nGenerating dashboard...")
    dashboard_path = analytics.generate_dashboard("dashboard.html")

    # Generate individual files too (optional)
    print("\nGenerating individual files...")
    analytics.save_csv(str(analytics.output_dir / "metrics.csv"))
    analytics.save_json(str(analytics.output_dir / "report.json"))

    # Generate separate plots (optional)
    analytics.plot_all()

    print(f"\nDashboard saved to: {dashboard_path}")
    print(f"All outputs saved to: {analytics.output_dir}")
    print("\n" + "=" * 80)


def example_2_plotting():
    """Example 2: Individual plot functions"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Individual Plotting")
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

    # Create analytics
    analytics = Analytics(results, df=df, name="Trend Following")

    # Plot individual charts (all go to timestamped folder)
    print("Generating individual plots...")

    analytics.plot_equity_curve()
    analytics.plot_drawdown()
    analytics.plot_monthly_returns()
    analytics.plot_pnl_distribution()

    print(f"\nAll plots saved to: {analytics.output_dir}")
    print("=" * 80)


def example_3_compare_strategies():
    """Example 3: Compare different strategies"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Compare Multiple Strategies")
    print("=" * 80)

    timeframe = "4h"
    period_days = 365
    fetcher = DataFetcher(exchange="binance")
    df = fetcher.fetch("BTC/USDT", timeframe, period_days=period_days)

    date_start = str(df.index[0])[:10]
    date_end = str(df.index[-1])[:10]

    # Run multiple strategies
    configs = {
        "Conservative": {
            "ema_fast": 55,
            "ema_slow": 200,
            "atr_period": 14,
            "atr_multiplier_sl": 0.5,
            "atr_multiplier_tp": 2.5,
            "rsi_period": 14,
            "position_size_pct": 0.5,
            "initial_capital": 10000.0,
            "timeframe": timeframe,
            "date_range": f"{date_start} to {date_end}",
        },
        "Balanced": {
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
        },
        "Aggressive": {
            "ema_fast": 30,
            "ema_slow": 100,
            "atr_period": 14,
            "atr_multiplier_sl": 0.8,
            "atr_multiplier_tp": 1.5,
            "rsi_period": 14,
            "position_size_pct": 0.9,
            "initial_capital": 10000.0,
            "timeframe": timeframe,
            "date_range": f"{date_start} to {date_end}",
        },
    }

    results_dict = {}
    for name, config in configs.items():
        strategy = TrendFollowingStrategy(config)
        engine = BacktestEngine({"initial_capital": 10000.0})
        results = engine.run(df, strategy)
        results_dict[name] = results

    # Compare strategies
    print("\nComparison Table:")
    compare_strategies(
        results_dict, metrics=["total_return", "sharpe_ratio", "max_drawdown"]
    )

    # Rank by Sharpe
    print("\nRanking by Sharpe Ratio:")
    ranked_df = rank_strategies(results_dict, by="sharpe_ratio")
    print(ranked_df.to_string())

    print("\n" + "=" * 80)


def example_4_compare_parameters():
    """Example 4: Compare parameter variations"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Compare Parameter Variations")
    print("=" * 80)

    timeframe = "4h"
    period_days = 180
    fetcher = DataFetcher(exchange="binance")
    df = fetcher.fetch("BTC/USDT", timeframe, period_days=period_days)

    date_start = str(df.index[0])[:10]
    date_end = str(df.index[-1])[:10]

    # Vary position size
    position_sizes = [0.3, 0.5, 0.7, 0.9]

    results_dict = {}
    for pos_size in position_sizes:
        config = {
            "ema_fast": 55,
            "ema_slow": 144,
            "atr_period": 14,
            "atr_multiplier_sl": 0.6,
            "atr_multiplier_tp": 2.0,
            "position_size_pct": pos_size,
            "initial_capital": 10000.0,
            "timeframe": timeframe,
            "date_range": f"{date_start} to {date_end}",
        }

        strategy = TrendFollowingStrategy(config)
        engine = BacktestEngine({"initial_capital": 10000.0})
        results = engine.run(df, strategy)

        name = f"Position Size {int(pos_size * 100)}%"
        results_dict[name] = results

    # Compare
    compare_strategies(
        results_dict, metrics=["total_return", "sharpe_ratio", "max_drawdown"]
    )

    # Rank by Sharpe
    rank_strategies(results_dict, by="sharpe_ratio")

    print("\n" + "=" * 80)


def example_5_full_comparison_report():
    """Example 5: Generate full comparison reports"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Generate Full Comparison Reports")
    print("=" * 80)

    timeframe = "4h"
    period_days = 365
    fetcher = DataFetcher(exchange="binance")
    df = fetcher.fetch("BTC/USDT", timeframe, period_days=period_days)

    date_start = str(df.index[0])[:10]
    date_end = str(df.index[-1])[:10]

    # Run 3 strategies
    configs = {
        "Strategy A": {
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
        },
        "Strategy B": {
            "ema_fast": 45,
            "ema_slow": 120,
            "atr_period": 14,
            "atr_multiplier_sl": 0.5,
            "atr_multiplier_tp": 2.2,
            "rsi_period": 14,
            "position_size_pct": 0.6,
            "initial_capital": 10000.0,
            "timeframe": timeframe,
            "date_range": f"{date_start} to {date_end}",
        },
        "Strategy C": {
            "ema_fast": 65,
            "ema_slow": 180,
            "atr_period": 14,
            "atr_multiplier_sl": 0.7,
            "atr_multiplier_tp": 1.8,
            "rsi_period": 14,
            "position_size_pct": 0.8,
            "initial_capital": 10000.0,
            "timeframe": timeframe,
            "date_range": f"{date_start} to {date_end}",
        },
    }

    results_dict = {}
    configs_dict = {}

    for name, config in configs.items():
        strategy = TrendFollowingStrategy(config)
        engine = BacktestEngine({"initial_capital": 10000.0})
        results = engine.run(df, strategy)

        results_dict[name] = results
        configs_dict[name] = config

    # Generate full comparison reports
    # Note: comparison reports use a separate directory (not timestamped)
    generate_comparison_reports(results_dict, output_dir="outputs/comparison_reports")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ANALYTICS MODULE EXAMPLES")
    print("=" * 80)
    print("\nNote: All examples use the new Analytics module")
    print("No print() statements needed - everything is automated!")
    print("\nAll outputs are saved to timestamped directories:")
    print("  outputs/YYYYMMDD_HHMMSS/strategy_name/")
    print("\n" + "=" * 80)

    # Create outputs directory
    import os

    os.makedirs("outputs", exist_ok=True)

    # Run examples
    example_1_basic_analytics()
    example_2_plotting()
    example_3_compare_strategies()
    example_4_compare_parameters()
    example_5_full_comparison_report()

    print("\n" + "=" * 80)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 80)
    print("\nCheck the 'outputs' directory for:")
    print("  - Timestamped directories with:")
    print("    * dashboard.html (single file with all charts)")
    print("    * metrics.csv, report.json")
    print("    * Individual HTML plots")
    print("  - Comparison reports (in outputs/comparison_reports/)")
    print("=" * 80)
