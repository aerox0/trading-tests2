"""Relative Strength Index indicator"""

from ..core.base_indicator import BaseIndicator
import pandas as pd
import numpy as np


class RSI(BaseIndicator):
    """Relative Strength Index indicator"""

    def calculate(self, df: pd.DataFrame, period: int = 14, **kwargs) -> pd.Series:
        """Calculate RSI

        Args:
            df: OHLCV DataFrame
            period: RSI period
            **kwargs: Additional parameters (ignored)

        Returns:
            Series with RSI values (0-100)
        """
        self._validate_period(period)

        # Calculate price changes
        delta = df["close"].diff()

        # Separate gains and losses
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        # Calculate RS and RSI
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def validate_params(self, **kwargs) -> bool:
        """Validate parameters"""
        if "period" in kwargs:
            self._validate_period(kwargs["period"])
        return True
