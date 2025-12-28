#!/usr/bin/env python3
"""
Data fetcher for BTC/USDT historical data for 1H timeframe
"""

import ccxt
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path


def fetch_btc_data_1h(symbol="BTC/USDT", period_days=730):
    """
    Fetch BTC/USDT 1H historical data from Binance

    Args:
        symbol (str): Trading symbol
        period_days (int): Number of days to fetch

    Returns:
        pd.DataFrame: Historical OHLCV data
    """
    exchange = ccxt.binance()

    end_time = int(datetime.now().timestamp() * 1000)
    start_time = end_time - (period_days * 24 * 60 * 60 * 1000)

    all_ohlcv = []
    current_time = start_time

    while current_time < end_time:
        limit = 1000
        ohlcv = exchange.fetch_ohlcv(
            symbol, timeframe="1h", since=current_time, limit=limit
        )

        if len(ohlcv) == 0:
            break

        all_ohlcv.extend(ohlcv)
        current_time = ohlcv[-1][0] + 1

    if len(all_ohlcv) == 0:
        raise ValueError(f"No data fetched from Binance for {symbol}")

    df = pd.DataFrame(
        all_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)

    print(f"Fetched {len(df)} 1H candles for {symbol}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")

    return df


def calculate_buy_and_hold_return(
    df: pd.DataFrame, initial_capital: float = 10000.0
) -> dict:
    """
    Calculate Buy and Hold return metrics

    Args:
        df (pd.DataFrame): OHLCV data
        initial_capital (float): Starting capital

    Returns:
        dict: Buy and Hold metrics
    """
    start_price = df["close"].iloc[0]
    end_price = df["close"].iloc[-1]

    total_return = (end_price - start_price) / start_price * 100
    final_value = initial_capital * (end_price / start_price)

    df["returns"] = df["close"].pct_change() * 100

    df["cumulative_returns"] = (1 + df["returns"] / 100.0).cumprod()
    running_max = df["cumulative_returns"].expanding().max()
    drawdown = (df["cumulative_returns"] - running_max) / running_max * 100
    max_drawdown = drawdown.min()

    returns_array = df["returns"].dropna().values

    sharpe_ratio = 0.0
    if len(returns_array) > 1:
        mean_return = sum(returns_array) / len(returns_array)
        std_return = (
            sum((x - mean_return) ** 2 for x in returns_array) / len(returns_array)
        ) ** 0.5
        sharpe_ratio = (mean_return / std_return) * (252**0.5) if std_return != 0 else 0

    metrics = {
        "start_price": start_price,
        "end_price": end_price,
        "total_return_pct": total_return,
        "initial_capital": initial_capital,
        "final_value": final_value,
        "max_drawdown_pct": max_drawdown,
        "sharpe_ratio": sharpe_ratio,
        "data_points": len(df),
    }

    print("\n" + "=" * 60)
    print("BUY AND HOLD BASELINE METRICS")
    print("=" * 60)
    print(f"Start Price: ${start_price:,.2f}")
    print(f"End Price: ${end_price:,.2f}")
    print(f"Total Return: {total_return:+.2f}%")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print(f"Final Value: ${final_value:,.2f}")
    print(f"Max Drawdown: {max_drawdown:.2f}%")
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    print("=" * 60)

    return metrics


if __name__ == "__main__":
    print("Fetching BTC/USDT 1H data...")
    df = fetch_btc_data_1h(symbol="BTC/USDT", period_days=730)

    print("\nData preview:")
    print(df.head())

    print("\nData summary:")
    print(df.describe())

    calculate_buy_and_hold_return(df, initial_capital=10000.0)
