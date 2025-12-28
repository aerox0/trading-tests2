"""Breakout strategy (placeholder)"""

from ..core.base_strategy import BaseStrategy
from ..indicators import EMA, ATR, RSI, Donchian
import pandas as pd


class BreakoutStrategy(BaseStrategy):
    """Donchian channel breakout strategy"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.ema = EMA()
        self.atr = ATR()
        self.donchian = Donchian()

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def execute_trade(self, df: pd.DataFrame, index: int):
        pass
