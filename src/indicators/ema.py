"""Exponential Moving Average indicator"""

from ..core.base_indicator import BaseIndicator
import pandas as pd


class EMA(BaseIndicator):
    """Exponential Moving Average indicator"""

    def calculate(self, df: pd.DataFrame, period: int = 20, **kwargs) -> pd.Series:
        """Calculate EMA

        Args:
            df: OHLCV DataFrame
            period: EMA period
            **kwargs: Additional parameters (ignored)

        Returns:
            Series with EMA values
        """
        self._validate_period(period)

        # Calculate EMA using pandas ewm
        ema = df["close"].ewm(span=period, adjust=False).mean()

        return ema

    def validate_params(self, **kwargs) -> bool:
        """Validate parameters"""
        if "period" in kwargs:
            self._validate_period(kwargs["period"])
        return True
