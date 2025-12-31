"""Optimize Smooth Trend 4H Strategy using Bayesian optimization

Finds optimal parameters for smooth, consistent returns.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, "/Users/aerox0/dev/trading-tests2")

import optuna
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.data.fetcher import DataFetcher
from src.strategies.smooth_trend_4h import SmoothTrend4HStrategy
from src.backtest.engine import BacktestEngine


def calculate_smoothness_objective(results):
    """Calculate objective function favoring smooth returns

    We want:
    - High Sharpe ratio (risk-adjusted returns)
    - High win rate (consistency)
    - Low max drawdown (smoothness)
    - Low standard deviation of returns (equity curve smoothness)
    """
    equity_curve = np.array(results["equity_curve"])
    returns = np.diff(equity_curve) / equity_curve[:-1]

    sharpe = results["sharpe_ratio"]
    win_rate = results["win_rate"]
    max_dd = abs(results["max_drawdown"])
    return_std = returns.std() * 100 if len(returns) > 0 else 0

    # Weighted objective: prioritize Sharpe and smoothness
    # Sharpe: 40% weight
    # Win Rate: 20% weight
    # Drawdown: 20% weight (penalize)
    # Smoothness: 20% weight (penalize return std)

    sharpe_score = sharpe
    win_rate_score = win_rate / 100
    drawdown_score = max(0, 1 - max_dd / 20)  # Normalize, penalize >20% DD
    smoothness_score = max(0, 1 - return_std)  # Penalize high std

    objective = (
        sharpe_score * 0.40
        + win_rate_score * 0.20
        + drawdown_score * 0.20
        + smoothness_score * 0.20
    )

    return objective


def optimize_smooth_trend(df, n_trials=200):
    """Optimize smooth trend strategy using Bayesian optimization"""

    def objective(trial):
        # Suggest parameters
        ema_fast = trial.suggest_int("ema_fast", 30, 80)
        ema_slow = trial.suggest_int("ema_slow", ema_fast + 20, 200)

        atr_sl = trial.suggest_float("atr_multiplier_sl", 0.3, 0.8)
        atr_tp = trial.suggest_float("atr_multiplier_tp", atr_sl * 2, 3.5)

        trail_mult = trial.suggest_float("trail_multiplier", 0.3, 0.8)

        rsi_period = trial.suggest_int("rsi_period", 7, 14)

        # RSI filters - wider ranges
        rsi_long_min = trial.suggest_int("rsi_long_min", 25, 40)
        rsi_long_max = trial.suggest_int("rsi_long_max", rsi_long_min + 15, 70)

        rsi_short_min = trial.suggest_int("rsi_short_min", 30, 45)
        rsi_short_max = trial.suggest_int("rsi_short_max", rsi_short_min + 15, 75)

        adx_threshold = trial.suggest_int("adx_threshold", 15, 30)

        volume_multiplier = trial.suggest_float("volume_multiplier", 0.9, 1.5)

        pullback_threshold = trial.suggest_float("pullback_threshold_pct", 0.008, 0.02)

        time_stop = trial.suggest_int("time_stop_bars", 5, 15)

        position_size = trial.suggest_float("position_size_pct", 0.4, 0.7)

        # Strategy config
        config = {
            "ema_fast": ema_fast,
            "ema_slow": ema_slow,
            "atr_period": 14,
            "atr_multiplier_sl": atr_sl,
            "atr_multiplier_tp": atr_tp,
            "trail_multiplier": trail_mult,
            "rsi_period": rsi_period,
            "rsi_long_min": rsi_long_min,
            "rsi_long_max": rsi_long_max,
            "rsi_short_min": rsi_short_min,
            "rsi_short_max": rsi_short_max,
            "adx_period": 14,
            "adx_threshold": adx_threshold,
            "volume_period": 20,
            "volume_multiplier": volume_multiplier,
            "pullback_threshold_pct": pullback_threshold,
            "time_stop_bars": time_stop,
            "position_size_pct": position_size,
            "initial_capital": 10000.0,
        }

        try:
            # Run backtest
            strategy = SmoothTrend4HStrategy(config)
            engine = BacktestEngine({"initial_capital": 10000.0})
            results = engine.run(df, strategy)

            # Calculate objective
            objective_value = calculate_smoothness_objective(results)

            return objective_value

        except Exception as e:
            # Penalize invalid configurations
            return -1.0

    print(f"\nRunning Bayesian optimization ({n_trials} trials)...")
    print("This may take a few minutes...")

    # Create study
    study = optuna.create_study(direction="maximize")

    # Optimize with progress bar
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    print(f"\nOptimization complete!")
    print(f"Best objective value: {study.best_value:.4f}")

    # Get best parameters
    best_params = study.best_params

    # Run final backtest with best params
    print("\nRunning final backtest with best parameters...")
    final_config = {
        **best_params,
        "atr_period": 14,
        "adx_period": 14,
        "volume_period": 20,
        "initial_capital": 10000.0,
    }

    strategy = SmoothTrend4HStrategy(final_config)
    engine = BacktestEngine({"initial_capital": 10000.0})
    final_results = engine.run(df, strategy)

    return {
        "best_params": best_params,
        "best_objective": study.best_value,
        "final_results": final_results,
        "n_trials": n_trials,
        "study": study,
    }


def main():
    print("=" * 80)
    print("SMOOTH TREND 4H - BAYESIAN OPTIMIZATION")
    print("=" * 80)

    # Fetch data
    print("\n[1/3] Fetching data...")
    fetcher = DataFetcher(exchange="binance")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)

    df = fetcher.fetch(
        symbol="BTC/USDT",
        timeframe="4h",
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )

    print(f"Data: {len(df)} candles from {df.index[0]} to {df.index[-1]}")

    # Run optimization
    print("\n[2/3] Running Bayesian optimization...")
    optimization_results = optimize_smooth_trend(df, n_trials=200)

    # Save results
    print("\n[3/3] Saving results...")

    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)

    # Save optimization results
    results_file = outputs_dir / "smooth_trend_4h_optimization.json"
    with open(results_file, "w") as f:
        json.dump(
            {
                "best_params": optimization_results["best_params"],
                "best_objective": float(optimization_results["best_objective"]),
                "n_trials": optimization_results["n_trials"],
                "final_metrics": {
                    "total_return": optimization_results["final_results"][
                        "total_return"
                    ],
                    "sharpe_ratio": optimization_results["final_results"][
                        "sharpe_ratio"
                    ],
                    "max_drawdown": optimization_results["final_results"][
                        "max_drawdown"
                    ],
                    "win_rate": optimization_results["final_results"]["win_rate"],
                    "total_trades": optimization_results["final_results"][
                        "total_trades"
                    ],
                    "final_capital": optimization_results["final_results"][
                        "final_capital"
                    ],
                },
            },
            f,
            indent=2,
            default=str,
        )

    print(f"✓ Saved: {results_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("OPTIMIZATION RESULTS")
    print("=" * 80)

    print("\nBest Parameters:")
    for key, value in optimization_results["best_params"].items():
        print(f"  {key}: {value}")

    print("\nFinal Backtest Performance:")
    print(
        f"  Total Return: {optimization_results['final_results']['total_return']:+.2f}%"
    )
    print(
        f"  Sharpe Ratio: {optimization_results['final_results']['sharpe_ratio']:.2f}"
    )
    print(
        f"  Max Drawdown: {optimization_results['final_results']['max_drawdown']:.2f}%"
    )
    print(f"  Win Rate: {optimization_results['final_results']['win_rate']:.1f}%")
    print(f"  Total Trades: {optimization_results['final_results']['total_trades']}")
    print(
        f"  Final Capital: ${optimization_results['final_results']['final_capital']:,.2f}"
    )

    print("\n" + "=" * 80)
    print("Optimization complete!")
    print("=" * 80)

    return optimization_results


if __name__ == "__main__":
    results = main()
