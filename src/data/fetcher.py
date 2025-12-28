"""Universal data fetcher for crypto exchanges"""

import ccxt
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class DataFetcher:
    """Universal data fetcher for multiple exchanges and timeframes

    Supports Binance, Coinbase, Kraken, Bybit and other ccxt-supported exchanges.
    Fetches OHLCV data for any symbol and timeframe.
    """

    SUPPORTED_EXCHANGES = ["binance", "coinbase", "kraken", "bybit", "okx", "kucoin"]
    SUPPORTED_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d", "1w", "1M"]

    def __init__(self, exchange: str = "binance"):
        """Initialize data fetcher

        Args:
            exchange: Exchange name (default: binance)

        Raises:
            ValueError: If exchange is not supported
        """
        exchange = exchange.lower()

        if exchange not in self.SUPPORTED_EXCHANGES:
            raise ValueError(
                f"Exchange '{exchange}' not supported. "
                f"Supported: {', '.join(self.SUPPORTED_EXCHANGES)}"
            )

        self.exchange_name = exchange
        self.exchange = getattr(ccxt, exchange)()
        self.exchange.enable_rate_limit = True

    def fetch(
        self,
        symbol: str,
        timeframe: str,
        period_days: int = 730,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch OHLCV data

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT', 'ETH/BTC')
            timeframe: Timeframe (e.g., '1h', '4h', '1d')
            period_days: Number of days to fetch (default: 730)
            start_date: Start date (optional, overrides period_days)
            end_date: End date (optional, default: now)

        Returns:
            DataFrame with OHLCV data indexed by timestamp

        Raises:
            ValueError: If timeframe is not supported
        """
        # Validate timeframe
        if timeframe not in self.SUPPORTED_TIMEFRAMES:
            raise ValueError(
                f"Timeframe '{timeframe}' not supported. "
                f"Supported: {', '.join(self.SUPPORTED_TIMEFRAMES)}"
            )

        # Calculate time range
        if start_date and end_date:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        else:
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=period_days)

        start_time = int(start_dt.timestamp() * 1000)
        end_time = int(end_dt.timestamp() * 1000)

        # Fetch data in batches
        all_ohlcv = []
        current_time = start_time
        limit = 1000  # Max candles per request

        while current_time < end_time:
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol, timeframe=timeframe, since=current_time, limit=limit
                )

                if len(ohlcv) == 0:
                    break

                all_ohlcv.extend(ohlcv)

                # Update current_time to last candle + 1ms
                current_time = ohlcv[-1][0] + 1

                # Stop if we've reached end_time
                if ohlcv[-1][0] >= end_time:
                    break

            except Exception as e:
                print(f"Warning: Error fetching data: {e}")
                break

        if len(all_ohlcv) == 0:
            raise ValueError(f"No data fetched from {self.exchange_name} for {symbol}")

        # Create DataFrame
        df = pd.DataFrame(
            all_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )

        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        # Remove duplicates (can happen with overlapping requests)
        df = df[~df.index.duplicated(keep="first")]

        # Sort by index
        df.sort_index(inplace=True)

        print(
            f"Fetched {len(df)} {timeframe} candles for {symbol} from {self.exchange_name}"
        )
        print(f"Date range: {df.index.min()} to {df.index.max()}")

        return df

    def fetch_multiple(
        self, symbols: List[str], timeframe: str, **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple symbols

        Args:
            symbols: List of trading symbols
            timeframe: Timeframe
            **kwargs: Additional arguments passed to fetch()

        Returns:
            Dictionary mapping symbols to DataFrames
        """
        data = {}

        for symbol in symbols:
            try:
                print(f"\nFetching {symbol}...")
                df = self.fetch(symbol, timeframe, **kwargs)
                data[symbol] = df
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")

        return data

    def calculate_buy_and_hold(
        self, df: pd.DataFrame, initial_capital: float = 10000.0
    ) -> Dict[str, float]:
        """Calculate Buy & Hold baseline metrics

        Args:
            df: OHLCV DataFrame
            initial_capital: Starting capital

        Returns:
            Dictionary with Buy & Hold metrics
        """
        start_price = df["close"].iloc[0]
        end_price = df["close"].iloc[-1]

        total_return = (end_price - start_price) / start_price * 100
        final_value = initial_capital * (end_price / start_price)

        # Calculate returns for Sharpe
        df["returns"] = df["close"].pct_change().fillna(0)

        # Calculate max drawdown
        cumulative = (1 + df["returns"]).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max * 100
        max_drawdown = drawdown.min()

        # Calculate Sharpe ratio (annualized)
        returns_array = df["returns"].values

        if len(returns_array) > 1 and returns_array.std() != 0:
            sharpe = (returns_array.mean() / returns_array.std()) * (
                len(returns_array) ** 0.5
            )
        else:
            sharpe = 0.0

        metrics = {
            "start_price": start_price,
            "end_price": end_price,
            "total_return_pct": total_return,
            "initial_capital": initial_capital,
            "final_value": final_value,
            "max_drawdown_pct": max_drawdown,
            "sharpe_ratio": sharpe,
            "data_points": len(df),
        }

        return metrics

    def __repr__(self) -> str:
        return f"DataFetcher(exchange={self.exchange_name})"
