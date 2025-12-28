#!/usr/bin/env python3
"""
Overfitting Analysis for Trend Following Strategy
Checks if grid search results are robust or overfitted
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from btc_data_fetcher import fetch_btc_data_4h, calculate_buy_and_hold_return
from trend_backtest_simple import TrendFollowingBacktest


def split_data_train_test(
    df: pd.DataFrame, train_pct: float = 0.7
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split data into training and testing sets"""
    split_idx = int(len(df) * train_pct)
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()
    return train_df, test_df


def walk_forward_analysis(
    df: pd.DataFrame, config: Dict, window_size: int = 1000, step: int = 500
) -> Dict:
    """
    Walk-forward analysis: train on sliding window, test on next period
    This simulates real trading by testing on out-of-sample data
    """
    print("\n" + "=" * 80)
    print("WALK-FORWARD ANALYSIS (Out-of-Sample Testing)")
    print("=" * 80)

    results = []

    for i in range(0, len(df) - window_size - step, step):
        train_df = df.iloc[i : i + window_size].copy()
        test_df = df.iloc[i + window_size : i + window_size + step].copy()

        if len(test_df) < 50:  # Skip if test period too short
            continue

        backtest_train = TrendFollowingBacktest(train_df, config)
        train_metrics = backtest_train.run()

        backtest_test = TrendFollowingBacktest(test_df, config)
        test_metrics = backtest_test.run()

        results.append(
            {
                "train_return": train_metrics.get("total_return", 0),
                "test_return": test_metrics.get("total_return", 0),
                "train_sharpe": train_metrics.get("sharpe_ratio", 0),
                "test_sharpe": test_metrics.get("sharpe_ratio", 0),
            }
        )

        print(
            f"  Period {len(results)}: Train {train_metrics.get('total_return', 0):+.2f}% "
            f"| Test {test_metrics.get('total_return', 0):+.2f}%"
        )

    if not results:
        print("  Not enough data for walk-forward analysis")
        return {}

    avg_train_return = np.mean([r["train_return"] for r in results])
    avg_test_return = np.mean([r["test_return"] for r in results])
    avg_train_sharpe = np.mean([r["train_sharpe"] for r in results])
    avg_test_sharpe = np.mean([r["test_sharpe"] for r in results])

    print(f"\nAverage Train Return: {avg_train_return:+.2f}%")
    print(f"Average Test Return: {avg_test_return:+.2f}%")
    print(
        f"Decay Factor: {avg_test_return / avg_train_return * 100 if avg_train_return != 0 else 0:.1f}%"
    )
    print(f"Average Train Sharpe: {avg_train_sharpe:.2f}")
    print(f"Average Test Sharpe: {avg_test_sharpe:.2f}")

    decay_score = avg_test_return / avg_train_return if avg_train_return != 0 else 0

    print("\n" + "=" * 80)
    if decay_score >= 0.6:
        print("✓ GOOD: Performance holds up on out-of-sample data")
    elif decay_score >= 0.4:
        print("⚠ MODERATE: Some performance decay on out-of-sample data")
    else:
        print("✗ OVERFITTING: Major performance decay on out-of-sample data")
    print("=" * 80)

    return {
        "avg_train_return": avg_train_return,
        "avg_test_return": avg_test_return,
        "decay_score": decay_score,
        "avg_train_sharpe": avg_train_sharpe,
        "avg_test_sharpe": avg_test_sharpe,
    }


def parameter_sensitivity_analysis(df: pd.DataFrame, best_config: Dict) -> None:
    """
    Test if small parameter changes cause large performance drops
    Robust strategies should have stable performance around optimal parameters
    """
    print("\n" + "=" * 80)
    print("PARAMETER SENSITIVITY ANALYSIS")
    print("=" * 80)

    # Get baseline performance with best config
    baseline_backtest = TrendFollowingBacktest(df, best_config)
    baseline = baseline_backtest.run()
    baseline_return = baseline.get("total_return", 0)
    baseline_sharpe = baseline.get("sharpe_ratio", 0)

    print(
        f"\nBaseline Performance: Return {baseline_return:+.2f}%, Sharpe {baseline_sharpe:.2f}"
    )

    # Test sensitivity by varying each parameter by ±20%
    sensitivity_results = []

    param_variations = {
        "ema_fast_period": [
            int(best_config["ema_fast_period"] * 0.8),
            int(best_config["ema_fast_period"] * 1.2),
        ],
        "ema_slow_period": [
            int(best_config["ema_slow_period"] * 0.8),
            int(best_config["ema_slow_period"] * 1.2),
        ],
        "atr_period": [
            max(5, int(best_config["atr_period"] * 0.8)),
            int(best_config["atr_period"] * 1.2),
        ],
        "atr_multiplier_sl": [
            best_config["atr_multiplier_sl"] * 0.8,
            best_config["atr_multiplier_sl"] * 1.2,
        ],
        "atr_multiplier_tp": [
            best_config["atr_multiplier_tp"] * 0.8,
            best_config["atr_multiplier_tp"] * 1.2,
        ],
        "rsi_period": [
            max(5, int(best_config["rsi_period"] * 0.8)),
            int(best_config["rsi_period"] * 1.2),
        ],
    }

    for param_name, variations in param_variations.items():
        for variation in variations:
            test_config = best_config.copy()
            test_config[param_name] = variation

            backtest = TrendFollowingBacktest(df, test_config)
            result = backtest.run()

            return_diff = result.get("total_return", 0) - baseline_return
            sharpe_diff = result.get("sharpe_ratio", 0) - baseline_sharpe

            sensitivity_results.append(
                {
                    "parameter": param_name,
                    "value": variation,
                    "return_diff": return_diff,
                    "sharpe_diff": sharpe_diff,
                }
            )

            print(
                f"  {param_name}: {variation} | Return {result.get('total_return', 0):+.2f}% "
                f"({return_diff:+.2f}) | Sharpe {result.get('sharpe_ratio', 0):.2f} ({sharpe_diff:+.2f})"
            )

    # Check if variations are within acceptable range
    max_return_drop = min([r["return_diff"] for r in sensitivity_results])
    max_sharpe_drop = min([r["sharpe_diff"] for r in sensitivity_results])

    print("\n" + "=" * 80)
    print(f"Max Return Drop: {max_return_drop:+.2f}%")
    print(f"Max Sharpe Drop: {max_sharpe_drop:+.2f}")

    if max_return_drop > -10 and max_sharpe_drop > -0.5:
        print("✓ GOOD: Performance stable with parameter variations")
    elif max_return_drop > -20 and max_sharpe_drop > -1.0:
        print("⚠ MODERATE: Some sensitivity to parameter changes")
    else:
        print("✗ OVERFITTING: Highly sensitive to parameter changes")
        print("  Strategy may not generalize to future data")
    print("=" * 80)


def monte_carlo_bootstrap(
    df: pd.DataFrame, config: Dict, n_simulations: int = 100
) -> None:
    """
    Monte Carlo bootstrap: Sample with replacement to test robustness
    A robust strategy should have consistent results across resampled data
    """
    print("\n" + "=" * 80)
    print(f"MONTE CARLO BOOTSTRAP ANALYSIS ({n_simulations} simulations)")
    print("=" * 80)

    results = []

    for i in range(n_simulations):
        # Sample with replacement (bootstrap)
        sampled_df = df.sample(frac=1.0, replace=True, random_state=i)
        sampled_df = sampled_df.sort_index()  # Maintain time order

        backtest = TrendFollowingBacktest(sampled_df, config)
        result = backtest.run()

        results.append(
            {
                "return": result.get("total_return", 0),
                "sharpe": result.get("sharpe_ratio", 0),
                "max_drawdown": result.get("max_drawdown", 0),
            }
        )

    returns = [r["return"] for r in results]
    sharpes = [r["sharpe"] for r in results]
    drawdowns = [r["max_drawdown"] for r in results]

    print(f"\nReturn Statistics:")
    print(f"  Mean: {np.mean(returns):+.2f}%")
    print(f"  Std: {np.std(returns):.2f}%")
    print(f"  Min: {np.min(returns):+.2f}%")
    print(f"  Max: {np.max(returns):+.2f}%")
    print(f"  Percentile 5: {np.percentile(returns, 5):+.2f}%")
    print(f"  Percentile 95: {np.percentile(returns, 95):+.2f}%")

    print(f"\nSharpe Ratio Statistics:")
    print(f"  Mean: {np.mean(sharpes):.2f}")
    print(f"  Std: {np.std(sharpes):.2f}")
    print(f"  Min: {np.min(sharpes):.2f}")
    print(f"  Max: {np.max(sharpes):.2f}")

    # Calculate coefficient of variation (lower = more stable)
    cv_return = (
        np.std(returns) / abs(np.mean(returns))
        if np.mean(returns) != 0
        else float("inf")
    )

    print("\n" + "=" * 80)
    print(f"Coefficient of Variation: {cv_return:.2f}")

    if cv_return < 0.5:
        print("✓ GOOD: Results are stable across different samples")
    elif cv_return < 1.0:
        print("⚠ MODERATE: Some variation across samples")
    else:
        print("✗ OVERFITTING: High variation - results may not generalize")
    print("=" * 80)


def train_test_split_analysis(
    df: pd.DataFrame, config: Dict, train_pct: float = 0.7
) -> None:
    """
    Simple train/test split to compare in-sample vs out-of-sample performance
    """
    print("\n" + "=" * 80)
    print(
        f"TRAIN/TEST SPLIT ANALYSIS ({int(train_pct * 100)}%/{int((1 - train_pct) * 100)}%)"
    )
    print("=" * 80)

    train_df, test_df = split_data_train_test(df, train_pct)

    print(f"\nTraining Data: {len(train_df)} bars")
    print(f"Test Data: {len(test_df)} bars")

    # Train on training data
    train_backtest = TrendFollowingBacktest(train_df, config)
    train_result = train_backtest.run()

    # Test on test data (out-of-sample)
    test_backtest = TrendFollowingBacktest(test_df, config)
    test_result = test_backtest.run()

    print("\n" + "-" * 80)
    print("Training (In-Sample) Results:")
    print(f"  Return: {train_result.get('total_return', 0):+.2f}%")
    print(f"  Sharpe: {train_result.get('sharpe_ratio', 0):.2f}")
    print(f"  Trades: {train_result.get('total_trades', 0)}")

    print("\nTest (Out-of-Sample) Results:")
    print(f"  Return: {test_result.get('total_return', 0):+.2f}%")
    print(f"  Sharpe: {test_result.get('sharpe_ratio', 0):.2f}")
    print(f"  Trades: {test_result.get('total_trades', 0)}")

    decay = test_result.get("total_return", 0) / train_result.get("total_return", 1)
    print("\n" + "=" * 80)
    print(f"Performance Decay: {decay * 100:.1f}%")

    if decay >= 0.7:
        print("✓ GOOD: Out-of-sample performance close to in-sample")
    elif decay >= 0.4:
        print("⚠ MODERATE: Some performance degradation expected")
    else:
        print("✗ OVERFITTING: Major performance drop on out-of-sample data")
    print("=" * 80)


def main():
    """Run comprehensive overfitting analysis"""
    print("=" * 80)
    print("OVERFITTING ANALYSIS FOR TREND FOLLOWING STRATEGY")
    print("=" * 80)

    # Best parameters from grid search
    best_config = {
        "ema_fast_period": 55,
        "ema_slow_period": 144,
        "atr_period": 14,
        "atr_multiplier_sl": 0.6,
        "atr_multiplier_tp": 2.5,
        "rsi_period": 14,
        "volume_multiplier": 1.0,
        "position_size_pct": 0.7,
    }

    print("\nFetching BTC/USDT 4H data...")
    df = fetch_btc_data_4h(symbol="BTC/USDT", period_days=730)

    print("\nTesting Configuration:")
    for k, v in best_config.items():
        print(f"  {k}: {v}")

    # Run all overfitting checks
    train_test_split_analysis(df, best_config)
    parameter_sensitivity_analysis(df, best_config)
    monte_carlo_bootstrap(df, best_config, n_simulations=50)
    walk_forward_analysis(df, best_config)

    # Overall assessment
    print("\n" + "=" * 80)
    print("OVERALL ASSESSMENT")
    print("=" * 80)
    print("If all tests show GOOD/MODERATE results:")
    print("  → Strategy is likely robust and not overfitted")
    print("\nIf multiple tests show OVERFITTING:")
    print("  → Consider:")
    print("     1. Using simpler parameters")
    print("     2. Reducing number of parameters")
    print("     3. Using different optimization metric (Sharpe vs Return)")
    print("     4. Collecting more training data")
    print("=" * 80)


if __name__ == "__main__":
    main()
