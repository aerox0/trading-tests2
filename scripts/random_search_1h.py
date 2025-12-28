#!/usr/bin/env python3
"""
Random Search Optimization for 1H Timeframe
Uses random sampling to find optimal parameters more efficiently
"""

import pandas as pd
import numpy as np
import random
from typing import Dict, Tuple
from btc_data_fetcher_1h import fetch_btc_data_1h, calculate_buy_and_hold_return
from trend_backtest_simple import (
    TrendFollowingBacktest,
    calculate_ema,
    calculate_atr,
    calculate_rsi,
)


def split_data_train_test(
    df: pd.DataFrame, train_pct: float = 0.7
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split data into training and testing sets"""
    split_idx = int(len(df) * train_pct)
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()
    return train_df, test_df


def run_backtest_on_data(df: pd.DataFrame, config: Dict) -> Dict:
    """Run backtest and return metrics"""
    backtest = TrendFollowingBacktest(df, config)
    results = backtest.run()

    if "sharpe_ratio" not in results or results["sharpe_ratio"] == 0:
        equity_curve = results["equity_curve"]
        returns = np.diff(equity_curve) / np.array(equity_curve[:-1])
        if len(returns) > 1 and returns.std() != 0:
            sharpe = (returns.mean() / returns.std()) * (len(returns) ** 0.5)
        else:
            sharpe = 0
        results["sharpe_ratio"] = sharpe

    return results


def calculate_combined_score(
    train_return: float, train_sharpe: float, test_return: float, test_sharpe: float
) -> float:
    """
    Combined score that rewards both return and Sharpe ratio
    Also penalizes overfitting (large train/test gap)
    """
    normalized_return = (train_return + test_return) / 2 / 100
    normalized_sharpe = (train_sharpe + test_sharpe) / 2 / 2

    overfitting_penalty = abs(train_return - test_return) / 100

    combined_score = (normalized_return * 0.5 + normalized_sharpe * 0.5) * (
        1 - overfitting_penalty
    )

    return max(0, combined_score)


def random_search(df: pd.DataFrame, n_iterations: int = 500) -> Tuple[Dict, Dict]:
    """
    Random search optimization for 1H timeframe
    More efficient than grid search for high-dimensional parameter spaces
    """
    print("\n" + "=" * 80)
    print(f"RANDOM SEARCH OPTIMIZATION (1H TIMEFRAME) - {n_iterations} iterations")
    print("=" * 80)

    train_df, test_df = split_data_train_test(df, train_pct=0.7)
    print(
        f"\nTraining Data: {len(train_df)} bars ({len(train_df) / len(df) * 100:.0f}%)"
    )
    print(f"Test Data: {len(test_df)} bars ({len(test_df) / len(df) * 100:.0f}%)")

    best_score = -float("inf")
    best_config = None
    best_train_metrics = None
    best_test_metrics = None

    all_results = []

    print(f"\nRunning {n_iterations} random iterations...\n")

    for iteration in range(n_iterations):
        # Random parameter sampling
        ema_fast = random.choice([20, 25, 30, 34, 40, 45, 50, 55, 60, 70])
        ema_slow = random.choice([80, 100, 120, 144, 168, 200, 250, 300])

        if ema_fast >= ema_slow:
            continue

        atr_sl = round(random.uniform(0.3, 0.8), 2)
        atr_tp = round(random.uniform(1.5, 4.0), 2)

        # Ensure reasonable R:R ratio
        if atr_tp < atr_sl * 2:
            continue

        rsi_period = random.choice([7, 10, 14, 21])
        vol_multiplier = round(random.uniform(0.8, 1.5), 2)
        pos_size = round(random.uniform(0.3, 0.8), 2)

        config = {
            "ema_fast_period": ema_fast,
            "ema_slow_period": ema_slow,
            "atr_period": 14,
            "atr_multiplier_sl": atr_sl,
            "atr_multiplier_tp": atr_tp,
            "rsi_period": rsi_period,
            "volume_multiplier": vol_multiplier,
            "position_size_pct": pos_size,
        }

        train_result = run_backtest_on_data(train_df, config)
        test_result = run_backtest_on_data(test_df, config)

        combined_score = calculate_combined_score(
            train_result.get("total_return", 0),
            train_result.get("sharpe_ratio", 0),
            test_result.get("total_return", 0),
            test_result.get("sharpe_ratio", 0),
        )

        all_results.append(
            {
                "config": config,
                "train_return": train_result.get("total_return", 0),
                "train_sharpe": train_result.get("sharpe_ratio", 0),
                "test_return": test_result.get("total_return", 0),
                "test_sharpe": test_result.get("sharpe_ratio", 0),
                "combined_score": combined_score,
            }
        )

        if iteration % 50 == 0 or iteration < 10:
            print(
                f"Iteration {iteration + 1}/{n_iterations}: "
                f"EMA({ema_fast},{ema_slow}) SL({atr_sl}) TP({atr_tp}) Size({pos_size * 100:.0f}%) | "
                f"Train {train_result.get('total_return', 0):+.1f}% Sharpe {train_result.get('sharpe_ratio', 0):.2f} | "
                f"Test {test_result.get('total_return', 0):+.1f}% Sharpe {test_result.get('sharpe_ratio', 0):.2f} | "
                f"Score {combined_score:.3f}"
            )

        if combined_score > best_score:
            best_score = combined_score
            best_config = config
            best_train_metrics = train_result
            best_test_metrics = test_result
            print(f"  *** NEW BEST *** Score: {combined_score:.4f}")

    all_results.sort(key=lambda x: x["combined_score"], reverse=True)

    print("\n" + "=" * 80)
    print("RANDOM SEARCH COMPLETE")
    print("=" * 80)

    print("\nTop 10 Configurations:")
    for i, result in enumerate(all_results[:10], 1):
        cfg = result["config"]
        print(
            f"\n{i}. EMA({cfg['ema_fast_period']},{cfg['ema_slow_period']}) "
            f"SL({cfg['atr_multiplier_sl']}) TP({cfg['atr_multiplier_tp']}) "
            f"RSI({cfg['rsi_period']}) Vol({cfg['volume_multiplier']}) Size({cfg['position_size_pct'] * 100:.0f}%)"
        )
        print(
            f"   Train: Return {result['train_return']:+.2f}%, Sharpe {result['train_sharpe']:.2f}, Trades {train_result.get('total_trades', 0)}"
        )
        print(
            f"   Test:  Return {result['test_return']:+.2f}%, Sharpe {result['test_sharpe']:.2f}, Trades {test_result.get('total_trades', 0)}"
        )
        print(f"   Combined Score: {result['combined_score']:.4f}")

    print("\n" + "=" * 80)
    print("BEST CONFIGURATION")
    print("=" * 80)
    print("\nParameters:")
    for k, v in best_config.items():
        print(f"  {k}: {v}")

    print(f"\nTraining Results (In-Sample):")
    print(f"  Return: {best_train_metrics.get('total_return', 0):+.2f}%")
    print(f"  Sharpe: {best_train_metrics.get('sharpe_ratio', 0):.2f}")
    print(f"  Trades: {best_train_metrics.get('total_trades', 0)}")

    print(f"\nTest Results (Out-of-Sample):")
    print(f"  Return: {best_test_metrics.get('total_return', 0):+.2f}%")
    print(f"  Sharpe: {best_test_metrics.get('sharpe_ratio', 0):.2f}")
    print(f"  Trades: {best_test_metrics.get('total_trades', 0)}")

    train_return = best_train_metrics.get("total_return", 0)
    test_return = best_test_metrics.get("total_return", 0)
    decay = test_return / train_return if train_return != 0 else 0

    print(f"\nOverfitting Analysis:")
    print(f"  Performance Decay: {decay * 100:.1f}%")
    if decay >= 0.7:
        print(f"  ✓ GOOD: Low overfitting")
    elif decay >= 0.5:
        print(f"  ⚠ MODERATE: Some overfitting")
    else:
        print(f"  ✗ HIGH: Significant overfitting")

    full_result = run_backtest_on_data(df, best_config)

    print(f"\n" + "=" * 80)
    print("FULL DATASET RESULTS")
    print("=" * 80)
    print(f"  Return: {full_result.get('total_return', 0):+.2f}%")
    print(f"  Sharpe: {full_result.get('sharpe_ratio', 0):.2f}")
    print(f"  Trades: {full_result.get('total_trades', 0)}")
    print("=" * 80)

    return best_config, {
        "train": best_train_metrics,
        "test": best_test_metrics,
        "full": full_result,
        "decay": decay,
        "all_results": all_results[:20],
    }


def main():
    """Run random search optimization for 1H"""
    print("Fetching BTC/USDT 1H data...")
    df = fetch_btc_data_1h(symbol="BTC/USDT", period_days=730)

    ba_h_metrics = calculate_buy_and_hold_return(df, initial_capital=10000.0)

    print("\nBuy & Hold Baseline:")
    print(f"  Return: {ba_h_metrics['total_return_pct']:+.2f}%")
    print(f"  Sharpe: {ba_h_metrics['sharpe_ratio']:.2f}")

    # Set random seed for reproducibility
    np.random.seed(42)
    random.seed(42)

    best_config, results = random_search(df, n_iterations=500)

    print("\n" + "=" * 80)
    print("COMPARISON WITH BUY & HOLD")
    print("=" * 80)
    print(f"Strategy Return: {results['full']['total_return']:+.2f}%")
    print(f"Buy & Hold Return: {ba_h_metrics['total_return_pct']:+.2f}%")
    print(
        f"Difference: {results['full']['total_return'] - ba_h_metrics['total_return_pct']:+.2f}%"
    )
    print("=" * 80)

    return best_config, results


if __name__ == "__main__":
    best_config, results = main()
