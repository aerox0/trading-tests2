"""Trend-following strategy using EMA pullback entries"""

from ..core.base_strategy import BaseStrategy
from ..indicators import EMA, ATR, RSI
from typing import Optional
import pandas as pd


class TrendFollowingStrategy(BaseStrategy):
    """Trend-following strategy with EMA pullback entries

    Strategy logic:
    - Detect trend using slow EMA
    - Enter when price pulls back to fast EMA
    - Exit with ATR-based SL/TP or trend reversal
    """

    def __init__(self, config: dict):
        super().__init__(config)

        # Initialize indicators
        self.ema = EMA()
        self.atr = ATR()
        self.rsi = RSI()

        # Validate config
        self.validate_config(config)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all indicators"""
        df = df.copy()

        # EMAs
        ema_fast_period = self.config.get("ema_fast", 50)
        ema_slow_period = self.config.get("ema_slow", 200)

        df["ema_fast"] = self.ema.calculate(df, ema_fast_period)
        df["ema_slow"] = self.ema.calculate(df, ema_slow_period)

        # ATR
        atr_period = self.config.get("atr_period", 14)
        df["atr"] = self.atr.calculate(df, atr_period)

        # RSI
        rsi_period = self.config.get("rsi_period", 14)
        df["rsi"] = self.rsi.calculate(df, rsi_period)

        # Volume average
        volume_period = self.config.get("volume_period", 20)
        df["volume_avg"] = df["volume"].rolling(window=volume_period).mean()

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate entry and exit signals"""
        # Trend direction
        df["is_bullish_trend"] = df["close"] > df["ema_slow"]
        df["is_bearish_trend"] = df["close"] < df["ema_slow"]

        # Pullback to fast EMA
        pullback_threshold = self.config.get("pullback_threshold_pct", 0.01)
        df["near_ema_fast"] = (
            abs(df["close"] - df["ema_fast"]) / df["close"] < pullback_threshold
        )

        # Volume confirmation
        volume_multiplier = self.config.get("volume_multiplier", 1.2)
        df["volume_confirmed"] = df["volume"] >= df["volume_avg"] * volume_multiplier

        # RSI filters
        rsi_overbought = self.config.get("rsi_overbought", 70)
        rsi_oversold = self.config.get("rsi_oversold", 30)

        df["rsi_long_ok"] = df["rsi"] < rsi_overbought
        df["rsi_short_ok"] = df["rsi"] > rsi_oversold

        # Entry signals
        df["long_signal"] = (
            df["is_bullish_trend"]
            & df["near_ema_fast"]
            & df["volume_confirmed"]
            & df["rsi_long_ok"]
        )

        df["short_signal"] = (
            df["is_bearish_trend"]
            & df["near_ema_fast"]
            & df["volume_confirmed"]
            & df["rsi_short_ok"]
        )

        # ATR-based stops
        atr_sl_mult = self.config.get("atr_multiplier_sl", 0.5)
        atr_tp_mult = self.config.get("atr_multiplier_tp", 2.0)

        df["atr_sl_distance"] = df["atr"] * atr_sl_mult
        df["atr_tp_distance"] = df["atr"] * atr_tp_mult

        return df

    def execute_trade(self, df: pd.DataFrame, index: int):
        """Execute trade logic for current bar"""
        row = df.iloc[index]
        close = row["close"]

        # Check exits first
        if self.position is not None:
            self._check_exit(df, index, close)

        # Check entries
        if self.position is None:
            if row["long_signal"]:
                self._enter_long(index, close, row)
            elif row["short_signal"]:
                self._enter_short(index, close, row)

        # Update equity curve
        self.equity_curve.append(self.capital)

    def _enter_long(self, i: int, close: float, row: pd.Series):
        """Enter long position"""
        atr_sl_distance = row["atr_sl_distance"]
        atr_tp_distance = row["atr_tp_distance"]

        position_size_pct = self.config.get("position_size_pct", 0.5)

        self.position = "long"
        self.entry_price = close
        self.position_size = self.capital * position_size_pct / close
        self.stop_loss = close - atr_sl_distance
        self.take_profit = close + atr_tp_distance

    def _enter_short(self, i: int, close: float, row: pd.Series):
        """Enter short position"""
        atr_sl_distance = row["atr_sl_distance"]
        atr_tp_distance = row["atr_tp_distance"]

        position_size_pct = self.config.get("position_size_pct", 0.5)

        self.position = "short"
        self.entry_price = close
        self.position_size = self.capital * position_size_pct / close
        self.stop_loss = close + atr_sl_distance
        self.take_profit = close - atr_tp_distance

    def _check_exit(self, df: pd.DataFrame, i: int, close: float):
        """Check exit conditions"""
        exit_reason = None

        if self.position == "long":
            if close <= self.stop_loss:
                exit_reason = "SL"
            elif close >= self.take_profit:
                exit_reason = "TP"
            elif not df.iloc[i]["is_bullish_trend"]:
                exit_reason = "Trend Change"

        elif self.position == "short":
            if close >= self.stop_loss:
                exit_reason = "SL"
            elif close <= self.take_profit:
                exit_reason = "TP"
            elif not df.iloc[i]["is_bearish_trend"]:
                exit_reason = "Trend Change"

        if exit_reason:
            self.close_position(close, exit_reason)
