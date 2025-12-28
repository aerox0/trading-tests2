"""Abstract base class for backtesting"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd


class BaseBacktest(ABC):
    """Abstract base class for backtesting engines

    Different backtesting engines can inherit from this class
    to provide different execution models (simple, vectorized, etc.)
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize backtest engine

        Args:
            config: Backtest configuration
        """
        self.config = config
        self.results = {}

    @abstractmethod
    def run(self, df: pd.DataFrame, strategy) -> Dict[str, Any]:
        """Run backtest with given strategy and data

        Args:
            df: OHLCV data
            strategy: Strategy instance

        Returns:
            Dictionary with backtest results
        """
        pass

    def validate_data(self, df: pd.DataFrame) -> bool:
        """Validate OHLCV data

        Args:
            df: DataFrame to validate

        Returns:
            True if valid, raises ValueError if invalid
        """
        required_columns = ["open", "high", "low", "close", "volume"]

        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        if len(df) == 0:
            raise ValueError("DataFrame is empty")

        if df.isnull().any().any():
            raise ValueError("DataFrame contains null values")

        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(config={self.config})"
