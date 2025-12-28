"""Donchian Channels indicator"""

from ..core.base_indicator import BaseIndicator
import pandas as pd


class Donchian(BaseIndicator):
    """Donchian Channels indicator"""

    def calculate(
        self, df: pd.DataFrame, period: int = 20, return_type: str = "middle", **kwargs
    ) -> pd.Series:
        """Calculate Donchian Channels

        Args:
            df: OHLCV DataFrame
            period: Lookback period
            return_type: 'upper', 'lower', or 'middle'
            **kwargs: Additional parameters (ignored)

        Returns:
            Series with Donchian channel values
        """
        self._validate_period(period)

        if return_type not in ["upper", "lower", "middle"]:
            raise ValueError(
                f"return_type must be 'upper', 'lower', or 'middle', got '{return_type}'"
            )

        # Calculate upper and lower channels
        upper = df["high"].rolling(window=period).max()
        lower = df["low"].rolling(window=period).min()

        if return_type == "upper":
            return upper
        elif return_type == "lower":
            return lower
        else:  # middle
            return (upper + lower) / 2

    def validate_params(self, **kwargs) -> bool:
        """Validate parameters"""
        if "period" in kwargs:
            self._validate_period(kwargs["period"])
        return True
