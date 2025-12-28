"""Average True Range indicator"""

from ..core.base_indicator import BaseIndicator
import pandas as pd
import numpy as np


class ATR(BaseIndicator):
    """Average True Range indicator"""

    def calculate(self, df: pd.DataFrame, period: int = 14, **kwargs) -> pd.Series:
        """Calculate ATR

        Args:
            df: OHLCV DataFrame
            period: ATR period
            **kwargs: Additional parameters (ignored)

        Returns:
            Series with ATR values
        """
        self._validate_period(period)

        high = df["high"]
        low = df["low"]
        close = df["close"]

        # Calculate True Range components
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        # True Range is max of three
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Average True Range
        atr = tr.rolling(window=period).mean()

        return atr

    def validate_params(self, **kwargs) -> bool:
        """Validate parameters"""
        if "period" in kwargs:
            self._validate_period(kwargs["period"])
        return True
