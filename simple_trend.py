#!/usr/bin/env python3
import pandas as pd
import numpy as np
from btc_data_fetcher import fetch_btc_data_4h, calculate_buy_and_hold_return

def calculate_ema(prices, period):
    return prices.ewm(span=period, adjust=False).mean()

def run_simple_trend_backtest(df, ema_fast=34, ema_slow=144, position_pct=1.0):
    """Simple trend following: always long when fast EMA > slow EMA"""
    df = df.copy()
    
    df["ema_fast"] = calculate_ema(df["close"], ema_fast)
    df["ema_slow"] = calculate_ema(df["close"], ema_slow)
    df["trend"] = np.where(df["ema_fast"] > df["ema_slow"], 1, 0)
    
    capital = 10000.0
    in_position = False
    position_size = 0.0
    equity_curve = [capital]
    
    for i in range(len(df)):
        if df["trend"].iloc[i] == 1 and not in_position:
            position_size = capital * position_pct / df["close"].iloc[i]
            in_position = True
        elif df["trend"].iloc[i] == 0 and in_position:
            capital += position_size * (df["close"].iloc[i] - df["close"].iloc[i-1])
            position_size = 0.0
            in_position = False
        
        if in_position:
            capital += position_size * (df["close"].iloc[i] - df["close"].iloc[i-1]) / 6
        
        equity_curve.append(capital)
    
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
    
    for ema_fast in [20, 34, 50, 100]:
        for ema_slow in [100, 144, 200]:
            if ema_fast >= ema_slow:
                continue
            
            for pos_pct in [0.5, 0.75, 1.0]:
                result = run_simple_trend_backtest(df, ema_fast, ema_slow, pos_pct)
                
                print(f"EMA({ema_fast},{ema_slow}) Size({pos_pct*100:.0f}%): "
                      f"{result['total_return']:+.2f}% | Sharpe: {result['sharpe_ratio']:.2f}")
                
                if best_result is None or result["total_return"] > best_result["total_return"]:
                    best_result = result
                    best_params = (ema_fast, ema_slow, pos_pct)
    
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
