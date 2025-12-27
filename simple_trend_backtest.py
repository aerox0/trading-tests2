#!/usr/bin/env python3
import pandas as pd
import numpy as np
from btc_data_fetcher import fetch_btc_data_4h, calculate_buy_and_hold_return


def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    return prices.ewm(span=period, adjust=False).mean()


def run_simple_trend_backtest(df, ema_fast=34, ema_slow=144, position_pct=1.0):
    """
    Simple trend following: always long when fast EMA > slow EMA
    Always short when fast EMA < slow EMA
    """
    df_copy = df.copy()

    df_copy["ema_fast"] = calculate_ema(df_copy["close"], ema_fast)
    df_copy["ema_slow"] = calculate_ema(df_copy["close"], ema_slow)
    df_copy["trend"] = np.where(df_copy["ema_fast"] > df_copy["ema_slow"], 1, 0)

    capital = 10000.0
    in_position = False
    position_size = 0.0
    equity_curve = [capital]
    position_type = None  # "long" or "short"

    for i in range(len(df_copy)):
        current_trend = df_copy["trend"].iloc[i]
        prev_trend = df_copy["trend"].iloc[i-1] if i > 0 else 0
        close = df_copy["close"].iloc[i]

        # Entry: trend change
        if current_trend != prev_trend and not in_position:
            if current_trend == 1:  # Bullish - go long
                position_size = capital * position_pct / close
                position_type = "long"
                in_position = True
            elif current_trend == 0:  # Bearish - go short
                position_size = capital * position_pct / close
                position_type = "short"
                in_position = True

        # Update position value
        if in_position:
            if position_type == "long":
                if i > 0:
                    capital += position_size * (close - df_copy["close"].iloc[i-1])
            else:
                capital += position_size * 0
            else:  # short
                if i > 0:
                    capital += position_size * (df_copy["close"].iloc[i-1] - close)
                else:
                    capital += position_size * 0

        equity_curve.append(capital)

    # Close any remaining position at end
    if in_position and len(equity_curve) > 1:
        capital += position_size * (df_copy["close"].iloc[-1] - df_copy["close"].iloc[-2])
        equity_curve[-1] = capital

    # Calculate metrics
    returns = np.diff(equity_curve) / np.array(equity_curve[:-1])

    if len(returns) > 1 and returns.std() != 0:
        sharpe = (returns.mean() / returns.std()) * (len(returns) ** 0.5)
    else:
        sharpe = 0

    equity_array = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_array)
    drawdown = (equity_array - running_max) / running_max * 100
    max_dd = drawdown.min()

    return {
        "total_return": (capital - 10000) / 10000 * 100,
        "final_capital": capital,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_dd,
        "equity_curve": equity_curve,
    }


if __name__ == "__main__":
    print("Fetching BTC/USDT 4H data...")
    df = fetch_btc_data_4h(symbol="BTC/USDT", period_days=730)

    ba_h_metrics = calculate_buy_and_hold_return(df, initial_capital=10000.0)

    print(f"\nBuy and Hold: {ba_h_metrics['total_return_pct']:+.2f}%")

    best_result = None
    best_params = None

    # Test different EMA combinations
    for ema_fast in [20, 34, 50]:
        for ema_slow in [100, 144, 200, 252]:
            if ema_fast >= ema_slow:
                continue

            for position_pct in [0.5, 0.75, 1.0]:
                result = run_simple_trend_backtest(df, ema_fast, ema_slow, position_pct)

                print(f"EMA({ema_fast},{ema_slow}) Size({position_pct*100:.0f}%): "
                      f"{result['total_return']:+.2f}% | Sharpe: {result['sharpe_ratio']:.2f}")

                if best_result is None or result["total_return"] > best_result["total_return"]:
                    best_result = result
                    best_params = (ema_fast, ema_slow, position_pct)

    print("\n" + "=" * 80)
    print("BEST RESULT")
    print("=" * 80)
    print(f"Parameters: EMA({best_params[0]},{best_params[1]}) Size({best_params[2]*100:.0f}%)")
    print(f"Total Return: {best_result['total_return']:+.2f}%")
    print(f"Buy & Hold: {ba_h_metrics['total_return_pct']:+.2f}%")
    print(f"Difference: {best_result['total_return'] - ba_h_metrics['total_return_pct']:+.2f}%")
    print(f"Sharpe Ratio: {best_result['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {best_result['max_drawdown']:.2f}%")

    if best_result['total_return'] >= ba_h_metrics['total_return_pct'] * 0.9:
        print("\n✓ Strategy beats or is within 90% of Buy and Hold!")
    else:
        print("\n✗ Strategy needs more optimization")
    print("=" * 80)
