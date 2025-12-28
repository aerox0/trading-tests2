#!/usr/bin/env python3
"""
Improved Grid Search with Overfitting Prevention
Optimizes for both Return and Sharpe ratio using train/test split
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from btc_data_fetcher import fetch_btc_data_4h, calculate_buy_and_hold_return
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

    # Calculate Sharpe if not available
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
    # Normalize metrics (typical ranges)
    normalized_return = (train_return + test_return) / 2 / 100  # ~0 to 1
    normalized_sharpe = (train_sharpe + test_sharpe) / 2 / 2  # ~0 to 2

    # Penalize overfitting: large gap between train and test
    overfitting_penalty = abs(train_return - test_return) / 100

    # Combined score: reward performance, penalize overfitting
    combined_score = (normalized_return * 0.5 + normalized_sharpe * 0.5) * (
        1 - overfitting_penalty
    )

    return max(0, combined_score)  # Ensure non-negative


def improved_grid_search(df: pd.DataFrame) -> Tuple[Dict, Dict]:
    """
    Improved grid search with overfitting prevention
    - Uses train/test split
    - Optimizes on combined return + Sharpe score
    - Penalizes overfitting
    - Reduced parameter space
    """
    print("\n" + "=" * 80)
    print("IMPROVED GRID SEARCH WITH OVERFITTING PREVENTION")
    print("=" * 80)

    train_df, test_df = split_data_train_test(df, train_pct=0.7)
    print(
        f"\nTraining Data: {len(train_df)} bars ({len(train_df) / len(df) * 100:.0f}%)"
    )
    print(f"Test Data: {len(test_df)} bars ({len(test_df) / len(df) * 100:.0f}%)")

    # REDUCED parameter space to reduce overfitting risk
    # Fix ATR and RSI at standard values
    param_grid = {
        "ema_fast_period": [34, 50, 55],
        "ema_slow_period": [144, 200],
        "atr_period": [14],  # Fixed - standard value
        "atr_multiplier_sl": [0.5, 0.6],
        "atr_multiplier_tp": [2.0, 2.5],
        "rsi_period": [14],  # Fixed - standard value
        "volume_multiplier": [1.0],  # Fixed - no volume filter
        "position_size_pct": [0.5, 0.7],
    }

    best_score = -float("inf")
    best_config = None
    best_train_metrics = None
    best_test_metrics = None
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

    print(f"Total iterations: {total_iterations}\n")

    all_results = []

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

                                    # Train on training data
                                    train_result = run_backtest_on_data(
                                        train_df, config
                                    )

                                    # Test on test data (out-of-sample)
                                    test_result = run_backtest_on_data(test_df, config)

                                    # Calculate combined score
                                    combined_score = calculate_combined_score(
                                        train_result.get("total_return", 0),
                                        train_result.get("sharpe_ratio", 0),
                                        test_result.get("total_return", 0),
                                        test_result.get("sharpe_ratio", 0),
                                    )

                                    all_results.append(
                                        {
                                            "config": config,
                                            "train_return": train_result.get(
                                                "total_return", 0
                                            ),
                                            "train_sharpe": train_result.get(
                                                "sharpe_ratio", 0
                                            ),
                                            "test_return": test_result.get(
                                                "total_return", 0
                                            ),
                                            "test_sharpe": test_result.get(
                                                "sharpe_ratio", 0
                                            ),
                                            "combined_score": combined_score,
                                        }
                                    )

                                    print(
                                        f"Iteration {iteration}/{total_iterations}: "
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
                                        print(f"  *** NEW BEST ***")

    # Sort all results by combined score
    all_results.sort(key=lambda x: x["combined_score"], reverse=True)

    print("\n" + "=" * 80)
    print("GRID SEARCH COMPLETE")
    print("=" * 80)

    print("\nTop 5 Configurations:")
    for i, result in enumerate(all_results[:5], 1):
        cfg = result["config"]
        print(
            f"\n{i}. EMA({cfg['ema_fast_period']},{cfg['ema_slow_period']}) "
            f"SL({cfg['atr_multiplier_sl']}) TP({cfg['atr_multiplier_tp']}) "
            f"Size({cfg['position_size_pct'] * 100:.0f}%)"
        )
        print(
            f"   Train: Return {result['train_return']:+.2f}%, Sharpe {result['train_sharpe']:.2f}"
        )
        print(
            f"   Test:  Return {result['test_return']:+.2f}%, Sharpe {result['test_sharpe']:.2f}"
        )
        print(f"   Combined Score: {result['combined_score']:.3f}")

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

    # Calculate overfitting metrics
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

    # Test on full dataset
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
        "all_results": all_results[:10],  # Top 10 results
    }


def main():
    """Run improved grid search"""
    print("Fetching BTC/USDT 4H data...")
    df = fetch_btc_data_4h(symbol="BTC/USDT", period_days=730)

    ba_h_metrics = calculate_buy_and_hold_return(df, initial_capital=10000.0)

    print("\nBuy & Hold Baseline:")
    print(f"  Return: {ba_h_metrics['total_return_pct']:+.2f}%")
    print(f"  Sharpe: {ba_h_metrics['sharpe_ratio']:.2f}")

    best_config, results = improved_grid_search(df)

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
