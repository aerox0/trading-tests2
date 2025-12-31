#!/usr/bin/env python3
"""
AI Analysis Backtest for Smooth Trend 4H Strategy

Generates analysis data (JSON/CSV) for AI optimization.
Last 2 years of 4H data.
"""

import sys
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, "/Users/aerox0/dev/trading-tests2")

from src.data.fetcher import DataFetcher
from src.strategies.smooth_trend_4h import SmoothTrend4HStrategy
from src.strategies.trend_following import TrendFollowingStrategy
from src.backtest.engine import BacktestEngine
from src.analytics.analyzer import ResultsAnalyzer


def run_backtest_analysis(strategy_class, config, df, name):
    """Run backtest and return detailed analysis results"""
    strategy = strategy_class(config)
    engine = BacktestEngine({"initial_capital": 10000.0})
    results = engine.run(df, strategy)

    analyzer = ResultsAnalyzer(results, df, name)
    analysis = analyzer.analyze()

    return {
        "strategy": name,
        "config": config,
        "metrics": analysis["basic"],
        "risk_metrics": analysis["risk"],
        "trading_stats": analysis["trading"],
        "monthly_stats": analysis.get("monthly", {}),
        "profit_dist": analysis["profit_dist"],
        "insights": analysis["insights"],
        "equity_curve": results["equity_curve"],
        "trades": results["trades"],
    }


def calculate_smoothness_metrics(equity_curve, trades):
    """Calculate metrics for equity curve smoothness"""
    equity_array = pd.Series(equity_curve)
    returns = equity_array.pct_change().dropna()

    smoothness = {
        "return_std": float(returns.std() * 100),
        "return_skewness": float(returns.skew()),
        "return_kurtosis": float(returns.kurtosis()),
        "max_consecutive_losses": calculate_max_consecutive_losses(trades),
        "largest_drawdown_duration_days": calculate_max_drawdown_duration(equity_curve),
        "monthly_volatility": calculate_monthly_volatility(equity_curve),
    }

    return smoothness


def calculate_max_consecutive_losses(trades):
    """Calculate maximum consecutive losing trades"""
    if not trades:
        return 0

    max_streak = 0
    current_streak = 0

    for trade in trades:
        if trade["pnl"] < 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    return max_streak


def calculate_max_drawdown_duration(equity_curve):
    """Calculate maximum duration of drawdown in bars"""
    equity_array = pd.Series(equity_curve)
    running_max = equity_array.expanding().max()
    drawdown = (equity_array - running_max) / running_max

    in_drawdown = drawdown < 0
    max_duration = 0
    current_duration = 0

    for is_dd in in_drawdown:
        if is_dd:
            current_duration += 1
            max_duration = max(max_duration, current_duration)
        else:
            current_duration = 0

    return max_duration


def calculate_monthly_volatility(equity_curve):
    """Calculate volatility of monthly returns"""
    equity_series = pd.Series(equity_curve)

    if len(equity_series) < 12:
        return 0.0

    # Sample every 90 bars (approx 1 month for 4H timeframe)
    monthly_returns = equity_series.iloc[::90].pct_change().dropna()
    return float(monthly_returns.std() * 100)


def main():
    print("=" * 80)
    print("SMOOTH TREND 4H - AI ANALYSIS BACKTEST")
    print("=" * 80)

    # Step 1: Fetch data (last 2 years of 4H)
    print("\n[1/5] Fetching data...")
    fetcher = DataFetcher(exchange="binance")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)

    df = fetcher.fetch(
        symbol="BTC/USDT",
        timeframe="4h",
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )

    print(f"Data range: {df.index[0]} to {df.index[-1]}")
    print(f"Total candles: {len(df)}")

    # Step 2: Configure Smooth Trend 4H Strategy (optimized)
    print("\n[2/5] Configuring Smooth Trend 4H Strategy...")
    smooth_config = {
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
        "name": "Smooth Trend 4H (Optimized)",
    }

    # Step 3: Configure Original Trend Strategy (for comparison)
    print("\n[3/5] Configuring Original Trend Strategy...")
    original_config = {
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
        "name": "Original Trend 4H",
    }

    # Step 4: Run backtests
    print("\n[4/5] Running backtests...")
    print("-" * 80)

    print("Running Smooth Trend 4H...")
    smooth_results = run_backtest_analysis(
        SmoothTrend4HStrategy, smooth_config, df, "Smooth Trend 4H"
    )
    print(f"  Return: {smooth_results['metrics']['total_return']:+.2f}%")
    print(f"  Sharpe: {smooth_results['metrics']['sharpe_ratio']:.2f}")
    print(f"  Trades: {smooth_results['metrics']['total_trades']}")

    print("\nRunning Original Trend 4H...")
    original_results = run_backtest_analysis(
        TrendFollowingStrategy, original_config, df, "Original Trend 4H"
    )
    print(f"  Return: {original_results['metrics']['total_return']:+.2f}%")
    print(f"  Sharpe: {original_results['metrics']['sharpe_ratio']:.2f}")
    print(f"  Trades: {original_results['metrics']['total_trades']}")

    # Step 5: Calculate Buy & Hold
    print("\nRunning Buy & Hold baseline...")
    buy_hold = fetcher.calculate_buy_and_hold(df)
    print(f"  Return: {buy_hold['total_return_pct']:+.2f}%")
    print(f"  Sharpe: {buy_hold['sharpe_ratio']:.2f}")

    # Step 6: Calculate smoothness metrics
    print("\n[5/5] Calculating smoothness metrics...")
    smooth_smoothness = calculate_smoothness_metrics(
        smooth_results["equity_curve"], smooth_results["trades"]
    )
    original_smoothness = calculate_smoothness_metrics(
        original_results["equity_curve"], original_results["trades"]
    )

    # Combine all results
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)

    comparison = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "symbol": "BTC/USDT",
            "timeframe": "4h",
            "period_days": 730,
            "start_date": df.index[0].isoformat(),
            "end_date": df.index[-1].isoformat(),
            "total_candles": len(df),
        },
        "buy_hold": buy_hold,
        "smooth_trend_4h": {
            **smooth_results,
            "smoothness": smooth_smoothness,
        },
        "original_trend_4h": {
            **original_results,
            "smoothness": original_smoothness,
        },
        "comparison": {
            "return_difference": smooth_results["metrics"]["total_return"]
            - original_results["metrics"]["total_return"],
            "sharpe_improvement": smooth_results["metrics"]["sharpe_ratio"]
            - original_results["metrics"]["sharpe_ratio"],
            "drawdown_improvement": smooth_results["metrics"]["max_drawdown"]
            - original_results["metrics"]["max_drawdown"],
            "win_rate_improvement": smooth_results["metrics"]["win_rate"]
            - original_results["metrics"]["win_rate"],
            "smoothness_improvement": {
                "return_std_diff": smooth_smoothness["return_std"]
                - original_smoothness["return_std"],
                "max_consecutive_losses_diff": smooth_smoothness[
                    "max_consecutive_losses"
                ]
                - original_smoothness["max_consecutive_losses"],
            },
        },
    }

    # Print comparison
    print(
        f"\nReturn: Smooth {smooth_results['metrics']['total_return']:+.2f}% vs Original {original_results['metrics']['total_return']:+.2f}% ({comparison['comparison']['return_difference']:+.2f}%)"
    )
    print(
        f"Sharpe: Smooth {smooth_results['metrics']['sharpe_ratio']:.2f} vs Original {original_results['metrics']['sharpe_ratio']:.2f} ({comparison['comparison']['sharpe_improvement']:+.2f})"
    )
    print(
        f"Drawdown: Smooth {smooth_results['metrics']['max_drawdown']:.2f}% vs Original {original_results['metrics']['max_drawdown']:.2f}% ({comparison['comparison']['drawdown_improvement']:+.2f}%)"
    )
    print(
        f"Win Rate: Smooth {smooth_results['metrics']['win_rate']:.1f}% vs Original {original_results['metrics']['win_rate']:.1f}% ({comparison['comparison']['win_rate_improvement']:+.1f}%)"
    )
    print(
        f"Max Consecutive Losses: Smooth {smooth_smoothness['max_consecutive_losses']} vs Original {original_smoothness['max_consecutive_losses']}"
    )
    print(
        f"Return Std Dev: Smooth {smooth_smoothness['return_std']:.2f}% vs Original {original_smoothness['return_std']:.2f}%"
    )

    # Step 7: Save analysis data
    print("\n" + "=" * 80)
    print("SAVING ANALYSIS DATA")
    print("=" * 80)

    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)

    # Save JSON (full analysis)
    json_file = outputs_dir / "smooth_trend_4h_analysis.json"
    with open(json_file, "w") as f:
        json.dump(comparison, f, indent=2, default=str)
    print(f"✓ Saved: {json_file}")

    # Save trades CSV
    smooth_trades_df = pd.DataFrame(smooth_results["trades"])
    smooth_trades_file = outputs_dir / "smooth_trend_4h_trades.csv"
    smooth_trades_df.to_csv(smooth_trades_file, index=False)
    print(f"✓ Saved: {smooth_trades_file}")

    original_trades_df = pd.DataFrame(original_results["trades"])
    original_trades_file = outputs_dir / "original_trend_4h_trades.csv"
    original_trades_df.to_csv(original_trades_file, index=False)
    print(f"✓ Saved: {original_trades_file}")

    # Save equity curve CSV
    equity_df = pd.DataFrame(
        {
            "smooth_trend": smooth_results["equity_curve"],
            "original_trend": original_results["equity_curve"],
            "buy_hold": [
                10000 * (df["close"].iloc[i] / df["close"].iloc[0])
                for i in range(len(df))
            ],
        }
    )
    equity_file = outputs_dir / "equity_curves.csv"
    equity_df.to_csv(equity_file)
    print(f"✓ Saved: {equity_file}")

    # Save OHLCV data (for TradingView import)
    ohlcv_file = outputs_dir / "btc_4h_ohlcv.csv"
    df.to_csv(ohlcv_file)
    print(f"✓ Saved: {ohlcv_file}")

    print("\n" + "=" * 80)
    print("BACKTEST COMPLETE")
    print("=" * 80)
    print(f"Analysis files saved to: {outputs_dir.absolute()}")

    return comparison


if __name__ == "__main__":
    results = main()
