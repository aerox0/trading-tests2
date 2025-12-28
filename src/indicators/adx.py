"""Average Directional Index indicator"""

from ..core.base_indicator import BaseIndicator
import pandas as pd


class ADX(BaseIndicator):
    """Average Directional Index indicator for trend strength"""

    def calculate(self, df: pd.DataFrame, period: int = 14, **kwargs) -> pd.Series:
        """Calculate ADX

        Args:
            df: OHLCV DataFrame
            period: ADX period
            **kwargs: Additional parameters (ignored)

        Returns:
            Series with ADX values (0-100)
        """
        self._validate_period(period)

        high = df["high"]
        low = df["low"]
        close = df["close"]

        # Calculate directional movement
        plus_dm = high.diff()
        minus_dm = low.diff()

        # Only consider positive directional movements
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        minus_dm = -minus_dm

        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Smooth True Range
        atr = tr.rolling(window=period).mean()

        # Calculate DI+ and DI-
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        # Calculate DX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)

        # Calculate ADX
        adx = dx.rolling(window=period).mean()

        return adx

    def validate_params(self, **kwargs) -> bool:
        """Validate parameters"""
        if "period" in kwargs:
            self._validate_period(kwargs["period"])
        return True
