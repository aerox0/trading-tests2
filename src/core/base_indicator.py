"""Abstract base class for all technical indicators"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import pandas as pd


class BaseIndicator(ABC):
    """Abstract base class for all technical indicators

    All indicators must inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self, name: Optional[str] = None):
        """Initialize indicator

        Args:
            name: Optional name for the indicator
        """
        self.name = name or self.__class__.__name__

    @abstractmethod
    def calculate(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        """Calculate indicator values

        Args:
            df: OHLCV DataFrame
            **kwargs: Indicator-specific parameters (period, etc.)

        Returns:
            Series of indicator values
        """
        pass

    def validate_params(self, **kwargs) -> bool:
        """Validate indicator parameters

        Args:
            **kwargs: Parameters to validate

        Returns:
            True if valid, raises ValueError if invalid
        """
        return True

    def _validate_period(self, period: int, min_period: int = 1, max_period: int = 500):
        """Validate period parameter

        Args:
            period: Period to validate
            min_period: Minimum allowed period
            max_period: Maximum allowed period

        Raises:
            ValueError: If period is invalid
        """
        if not isinstance(period, int):
            raise ValueError(f"Period must be an integer, got {type(period)}")
        if period < min_period:
            raise ValueError(f"Period must be >= {min_period}, got {period}")
        if period > max_period:
            raise ValueError(f"Period must be <= {max_period}, got {period}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
