#!/usr/bin/env python3
"""
Data fetcher for BTC/USDT historical data using Yahoo Finance
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def fetch_btc_data(period="2y", interval="1d"):
    """
    Fetch BTC/USDT historical data from Yahoo Finance

    Args:
        period (str): Data period (e.g., "1y", "2y", "5y", "max")
        interval (str): Data interval (e.g., "1d", "1h", "15m")

    Returns:
        pd.DataFrame: Historical price data with required columns
    """
    try:
        # Fetch BTC/USDT data from Yahoo Finance
        btc_symbol = "BTC-USD"
        btc_data = yf.download(btc_symbol, period=period, interval=interval)

        if btc_data.empty:
            raise ValueError("No data fetched from Yahoo Finance")

        # Rename columns to match backtesting.py requirements
        btc_data.rename(
            columns={
                "Open": "Open",
                "High": "High",
                "Low": "Low",
                "Close": "Close",
                "Volume": "Volume",
            },
            inplace=True,
        )

        # Ensure all required columns exist
        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        for col in required_columns:
            if col not in btc_data.columns:
                raise ValueError(f"Missing required column: {col}")

        print(f"Successfully fetched {len(btc_data)} days of BTC/USDT data")
        print(f"Date range: {btc_data.index.min()} to {btc_data.index.max()}")

        return btc_data

    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


def get_sample_data():
    """
    Generate sample BTC/USDT data for testing if Yahoo Finance is unavailable
    """
    # Create sample data for testing
    dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
    n_days = len(dates)

    # Generate sample price data with some trend and volatility
    import numpy as np

    np.random.seed(42)

    # Starting price around $40,000
    base_price = 40000
    prices = []
    current_price = base_price

    for i in range(n_days):
        # Random walk with slight upward bias
        change = np.random.normal(0.001, 0.02)  # 0.1% daily drift, 2% volatility
        current_price = current_price * (1 + change)
        prices.append(current_price)

    # Create OHLC data
    data = []
    for i, price in enumerate(prices):
        # Add some intraday volatility
        open_price = price * (1 + np.random.normal(0, 0.005))
        high_price = max(open_price, price * (1 + abs(np.random.normal(0, 0.01))))
        low_price = min(open_price, price * (1 - abs(np.random.normal(0, 0.01))))
        close_price = price

        data.append(
            {
                "Date": dates[i],
                "Open": open_price,
                "High": high_price,
                "Low": low_price,
                "Close": close_price,
                "Volume": np.random.randint(1000, 10000),
            }
        )

    df = pd.DataFrame(data)
    df.set_index("Date", inplace=True)

    return df


if __name__ == "__main__":
    # Test data fetching
    print("Fetching BTC/USDT data from Yahoo Finance...")
    data = fetch_btc_data(period="1y", interval="1d")

    if data is not None:
        print("\nData preview:")
        print(data.head())
        print(f"\nData shape: {data.shape}")
        print(f"Columns: {list(data.columns)}")
    else:
        print("Using sample data instead...")
        data = get_sample_data()
        print(data.head())
