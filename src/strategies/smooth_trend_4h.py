"""Smooth Trend 4H Strategy - Designed for consistent returns with smoother equity curve

Key improvements over standard trend following:
1. Higher win rate through tighter R:R ratio
2. Trend strength filter (ADX) to avoid weak trends
3. Multi-entry scaling to reduce single-trade impact
4. Dynamic trailing stops to lock in profits
5. Volatility-based position sizing
6. Enhanced entry filters
"""

from ..core.base_strategy import BaseStrategy
from ..indicators import EMA, ATR, RSI, ADX
from typing import Optional, Dict, Any
import pandas as pd


class SmoothTrend4HStrategy(BaseStrategy):
    """Smooth trend strategy for 4H timeframe

    Philosophy: Many small wins > few big wins

    Goals:
    - Higher win rate (45-55%)
    - Smoother equity curve
    - Reduced drawdowns
    - Consistent monthly performance
    """

    def __init__(self, config: dict):
        super().__init__(config)

        self.ema = EMA()
        self.atr = ATR()
        self.rsi = RSI()
        self.adx = ADX()

        self.validate_config(config)

        # Position scaling state
        self.entry_scale_1 = 0.0
        self.entry_scale_2 = 0.0
        self.entry_scale_3 = 0.0
        self.current_scale = 1
        self.trail_start_price = None

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # EMAs
        ema_fast_period = self.config.get("ema_fast", 45)
        ema_slow_period = self.config.get("ema_slow", 120)

        df["ema_fast"] = self.ema.calculate(df, ema_fast_period)
        df["ema_slow"] = self.ema.calculate(df, ema_slow_period)

        # ATR
        atr_period = self.config.get("atr_period", 14)
        df["atr"] = self.atr.calculate(df, atr_period)

        # ATR as % of price (for volatility sizing)
        df["atr_pct"] = (df["atr"] / df["close"]) * 100

        # RSI
        rsi_period = self.config.get("rsi_period", 7)
        df["rsi"] = self.rsi.calculate(df, rsi_period)

        # ADX
        adx_period = self.config.get("adx_period", 14)
        df["adx"] = self.adx.calculate(df, adx_period)

        # Volume average
        volume_period = self.config.get("volume_period", 20)
        df["volume_avg"] = df["volume"].rolling(window=volume_period).mean()

        # EMA alignment (both EMAs same direction)
        df["ema_aligned"] = (df["ema_fast"] > df["ema_slow"]) == (
            df["close"] > df["ema_slow"]
        )

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        # Trend direction
        df["is_bullish_trend"] = df["close"] > df["ema_slow"]
        df["is_bearish_trend"] = df["close"] < df["ema_slow"]

        # EMA alignment
        df["ema_bullish_aligned"] = df["ema_fast"] > df["ema_slow"]
        df["ema_bearish_aligned"] = df["ema_fast"] < df["ema_slow"]

        # Trend strength filter (ADX)
        adx_threshold = self.config.get("adx_threshold", 25)
        df["strong_trend"] = df["adx"] >= adx_threshold

        # Pullback to fast EMA (tighter threshold for 4H)
        pullback_threshold = self.config.get("pullback_threshold_pct", 0.008)
        df["near_ema_fast"] = (
            abs(df["close"] - df["ema_fast"]) / df["close"] < pullback_threshold
        )

        # Enhanced volume confirmation (higher multiplier for quality)
        volume_multiplier = self.config.get("volume_multiplier", 1.3)
        df["volume_confirmed"] = df["volume"] >= df["volume_avg"] * volume_multiplier

        # RSI range filter (avoid extremes, prefer mid-range pullbacks)
        rsi_long_min = self.config.get("rsi_long_min", 40)
        rsi_long_max = self.config.get("rsi_long_max", 60)
        rsi_short_min = self.config.get("rsi_short_min", 40)
        rsi_short_max = self.config.get("rsi_short_max", 60)

        df["rsi_long_ok"] = (df["rsi"] >= rsi_long_min) & (df["rsi"] <= rsi_long_max)
        df["rsi_short_ok"] = (df["rsi"] >= rsi_short_min) & (df["rsi"] <= rsi_short_max)

        # Entry signals (all conditions must be met)
        df["long_signal"] = (
            df["is_bullish_trend"]
            & df["ema_bullish_aligned"]
            & df["strong_trend"]
            & df["near_ema_fast"]
            & df["volume_confirmed"]
            & df["rsi_long_ok"]
        )

        df["short_signal"] = (
            df["is_bearish_trend"]
            & df["ema_bearish_aligned"]
            & df["strong_trend"]
            & df["near_ema_fast"]
            & df["volume_confirmed"]
            & df["rsi_short_ok"]
        )

        # Scale-in signals (second and third entries)
        df["scale_long_2"] = df["long_signal"] & (df["close"] < df["ema_fast"])
        df["scale_long_3"] = df["long_signal"] & (df["rsi"] < rsi_long_min + 5)

        df["scale_short_2"] = df["short_signal"] & (df["close"] > df["ema_fast"])
        df["scale_short_3"] = df["short_signal"] & (df["rsi"] > rsi_short_max - 5)

        # ATR-based stops
        atr_sl_mult = self.config.get("atr_multiplier_sl", 0.4)
        atr_tp_mult = self.config.get("atr_multiplier_tp", 1.2)
        trail_mult = self.config.get("trail_multiplier", 0.4)

        df["atr_sl_distance"] = df["atr"] * atr_sl_mult
        df["atr_tp_distance"] = df["atr"] * atr_tp_mult
        df["trail_distance"] = df["atr"] * trail_mult

        # Time stop (exit if trade hasn't hit TP after N bars)
        df["time_stop_bars"] = self.config.get("time_stop_bars", 5)

        return df

    def execute_trade(self, df: pd.DataFrame, index: int):
        row = df.iloc[index]
        close = row["close"]

        # Check exits first
        if self.position is not None:
            self._check_exit(df, index, close, row)

        # Check entries
        if self.position is None:
            if row["long_signal"]:
                self._enter_long_initial(index, close, row)
            elif row["short_signal"]:
                self._enter_short_initial(index, close, row)
        else:
            # Check for scale-in opportunities
            self._check_scale_in(df, index, close, row)

        # Update equity curve
        self.equity_curve.append(self.capital)

    def _get_position_size(self, price: float, atr_pct: float, row: pd.Series) -> float:
        """Dynamic position sizing based on volatility

        High volatility -> smaller position
        Low volatility -> larger position
        """
        base_pct = self.config.get("position_size_pct", 0.5)

        if atr_pct > 1.0:
            size_pct = base_pct * 0.8
        elif atr_pct > 0.5:
            size_pct = base_pct
        else:
            size_pct = base_pct * 1.2

        return self.capital * size_pct / price

    def _enter_long_initial(self, i: int, close: float, row: pd.Series):
        atr_sl_distance = row["atr_sl_distance"]
        atr_tp_distance = row["atr_tp_distance"]

        atr_pct = row["atr_pct"]
        base_position_size = self._get_position_size(close, atr_pct, row)

        # Initial entry (50% of base position)
        self.position = "long"
        self.entry_price = close
        self.entry_time = row.name
        self.position_size = base_position_size * 0.5
        self.entry_scale_1 = close
        self.current_scale = 1

        self.stop_loss = close - atr_sl_distance
        self.take_profit = close + atr_tp_distance
        self.trail_start_price = None

    def _enter_short_initial(self, i: int, close: float, row: pd.Series):
        atr_sl_distance = row["atr_sl_distance"]
        atr_tp_distance = row["atr_tp_distance"]

        atr_pct = row["atr_pct"]
        base_position_size = self._get_position_size(close, atr_pct, row)

        self.position = "short"
        self.entry_price = close
        self.entry_time = row.name
        self.position_size = base_position_size * 0.5
        self.entry_scale_1 = close
        self.current_scale = 1

        self.stop_loss = close + atr_sl_distance
        self.take_profit = close - atr_tp_distance
        self.trail_start_price = None

    def _check_scale_in(self, df: pd.DataFrame, i: int, close: float, row: pd.Series):
        """Check for scale-in opportunities (second and third entries)"""
        if self.current_scale >= 3:
            return

        atr_pct = row["atr_pct"]
        base_position_size = self._get_position_size(close, atr_pct, row)

        if self.position == "long" and row["scale_long_2"] and self.current_scale == 1:
            scale_size = base_position_size * 0.3
            avg_price = (
                (self.entry_price * self.position_size) + (close * scale_size)
            ) / (self.position_size + scale_size)
            self.position_size += scale_size
            self.entry_price = avg_price
            self.entry_scale_2 = close
            self.current_scale = 2

        elif (
            self.position == "long" and row["scale_long_3"] and self.current_scale == 2
        ):
            scale_size = base_position_size * 0.2
            avg_price = (
                (self.entry_price * self.position_size) + (close * scale_size)
            ) / (self.position_size + scale_size)
            self.position_size += scale_size
            self.entry_price = avg_price
            self.entry_scale_3 = close
            self.current_scale = 3

        elif (
            self.position == "short"
            and row["scale_short_2"]
            and self.current_scale == 1
        ):
            scale_size = base_position_size * 0.3
            avg_price = (
                (self.entry_price * self.position_size) + (close * scale_size)
            ) / (self.position_size + scale_size)
            self.position_size += scale_size
            self.entry_price = avg_price
            self.entry_scale_2 = close
            self.current_scale = 2

        elif (
            self.position == "short"
            and row["scale_short_3"]
            and self.current_scale == 2
        ):
            scale_size = base_position_size * 0.2
            avg_price = (
                (self.entry_price * self.position_size) + (close * scale_size)
            ) / (self.position_size + scale_size)
            self.position_size += scale_size
            self.entry_price = avg_price
            self.entry_scale_3 = close
            self.current_scale = 3

    def _check_exit(self, df: pd.DataFrame, i: int, close: float, row: pd.Series):
        exit_reason = None

        if self.position == "long":
            # Update trailing stop after half profit
            if (
                self.trail_start_price is None
                and close
                >= self.entry_price + (self.take_profit - self.entry_price) * 0.5
            ):
                self.trail_start_price = close

            if self.trail_start_price is not None:
                new_trail = close - row["trail_distance"]
                if new_trail > self.stop_loss:
                    self.stop_loss = new_trail

            # Exit conditions - simplified
            if close <= self.stop_loss:
                exit_reason = "SL"
            elif close >= self.take_profit:
                exit_reason = "TP"
            elif not df.iloc[i]["is_bullish_trend"]:
                exit_reason = "Trend Change"

        elif self.position == "short":
            # Update trailing stop after half profit
            if (
                self.trail_start_price is None
                and close
                <= self.entry_price + (self.take_profit - self.entry_price) * 0.5
            ):
                self.trail_start_price = close

            if self.trail_start_price is not None:
                new_trail = close + row["trail_distance"]
                if new_trail < self.stop_loss:
                    self.stop_loss = new_trail

            if close >= self.stop_loss:
                exit_reason = "SL"
            elif close <= self.take_profit:
                exit_reason = "TP"
            elif not df.iloc[i]["is_bearish_trend"]:
                exit_reason = "Trend Change"

        elif self.position == "short":
            # Update trailing stop after half profit
            if (
                self.trail_start_price is None
                and close
                <= self.entry_price + (self.take_profit - self.entry_price) * 0.5
            ):
                self.trail_start_price = close

            if self.trail_start_price is not None:
                new_trail = close + row["trail_distance"]
                if new_trail < self.stop_loss:
                    self.stop_loss = new_trail

            if close >= self.stop_loss:
                exit_reason = "SL"
            elif close <= self.take_profit:
                exit_reason = "TP"
            elif not df.iloc[i]["is_bearish_trend"]:
                exit_reason = "Trend Change"
            elif df.iloc[i]["adx"] < 20:
                exit_reason = "Trend Weakness"
            elif i - df.index.get_loc(self.entry_time) >= row["time_stop_bars"]:
                exit_reason = "Time Stop"

        if exit_reason:
            trade = self.close_position(close, exit_reason, exit_time=df.iloc[i].name)
            trade["scales"] = self.current_scale
            trade["scale_prices"] = [
                self.entry_scale_1,
                self.entry_scale_2,
                self.entry_scale_3,
            ][: self.current_scale]
