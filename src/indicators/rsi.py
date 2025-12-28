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
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Use Wilder's smoothing (ewm with alpha = 1/period)
        alpha = 1.0 / period
        avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
        avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()

        # Calculate RS
        # When avg_loss is 0, RSI should be 100 (no losses)
        # When both are 0, RSI should be 50 (neutral)
        rs = avg_gain / avg_loss.replace(0, np.nan)

        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))

        # Handle special cases
        # When avg_loss is 0 (all gains), RSI = 100
        # When avg_gain is 0 (all losses), RSI = 0
        # When both are 0, RSI = 50
        rsi = rsi.where(avg_loss != 0, 100)  # When loss is 0, RSI = 100
        rsi = rsi.where((avg_gain != 0) | (avg_loss != 0), 50)  # When both 0, RSI = 50

        return rsi

    def validate_params(self, **kwargs) -> bool:
        """Validate parameters"""
        if "period" in kwargs:
            self._validate_period(kwargs["period"])
        return True
