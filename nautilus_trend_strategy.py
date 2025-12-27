#!/usr/bin/env python3
"""
Trend-Following Strategy for Nautilus Trader
Combines EMA trend following with volatility regime detection
"""

from decimal import Decimal
from typing import Optional

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy


class TrendFollowingConfig(StrategyConfig, frozen=True):
    instrument_id: str
    bar_type: str
    trade_size: Decimal = Decimal("0.1")

    ema_fast_period: int = 50
    ema_slow_period: int = 200

    atr_period: int = 14
    atr_multiplier_sl: float = 0.5
    atr_multiplier_tp: float = 2.0

    risk_reward_ratio: float = 2.0

    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0

    volume_period: int = 20
    volume_multiplier: float = 1.2

    position_size_pct: float = 0.5

    ema_fast: float = 0.0
    ema_slow: float = 0.0


class TrendFollowingStrategy(Strategy):
    config: TrendFollowingConfig

    def __init__(self, config: TrendFollowingConfig) -> None:
        super().__init__(config)

        self.close_prices: list[float] = []
        self.high_prices: list[float] = []
        self.low_prices: list[float] = []
        self.volumes: list[float] = []

        self.ema_fast: float = 0.0
        self.ema_slow: float = 0.0
        self.atr: float = 0.0
        self.rsi: float = 50.0
        self.volume_avg: float = 0.0

        self.in_position = False
        self.entry_price: Optional[float] = None
        self.stop_loss_price: Optional[float] = None
        self.take_profit_price: Optional[float] = None

        self._ema_fast_initialized = False
        self._ema_slow_initialized = False

    def on_start(self) -> None:
        self.subscribe_bars(self.config.bar_type)
        self.log.info(
            f"Trend Following Strategy started on {self.config.instrument_id}"
        )
        self.log.info(
            f"Parameters: EMA({self.config.ema_fast_period}, {self.config.ema_slow_period}), "
            f"ATR({self.config.atr_period}), RSI({self.config.rsi_period})"
        )

    def on_bar(self, bar: Bar) -> None:
        self.close_prices.append(float(bar.close))
        self.high_prices.append(float(bar.high))
        self.low_prices.append(float(bar.low))
        self.volumes.append(float(bar.volume))

        min_periods = max(
            self.config.ema_slow_period,
            self.config.atr_period,
            self.config.rsi_period,
            self.config.volume_period,
        )

        if len(self.close_prices) < min_periods:
            return

        self._calculate_indicators()

        if self.in_position:
            self._manage_position(bar)
        else:
            self._check_entry_signals(bar)

    def _calculate_indicators(self) -> None:
        close = self.close_prices[-1]
        closes = self.close_prices

        if len(closes) < self.config.ema_slow_period:
            return

        ema_fast = self._calculate_ema(closes, self.config.ema_fast_period)
        ema_slow = self._calculate_ema(closes, self.config.ema_slow_period)

        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self._ema_fast_initialized = True
        self._ema_slow_initialized = True

        atr = self._calculate_atr(
            self.high_prices[-self.config.atr_period :],
            self.low_prices[-self.config.atr_period :],
            closes[-self.config.atr_period :],
        )
        self.atr = atr

        rsi = self._calculate_rsi(closes, self.config.rsi_period)
        self.rsi = rsi

        volumes = self.volumes[-self.config.volume_period :]
        self.volume_avg = sum(volumes) / len(volumes)

    def _calculate_ema(self, prices: list[float], period: int) -> float:
        multiplier = 2.0 / (period + 1)

        if period == self.config.ema_fast_period:
            prev_ema = self.ema_fast
            is_initialized = self._ema_fast_initialized
        else:
            prev_ema = self.ema_slow
            is_initialized = self._ema_slow_initialized

        if not is_initialized:
            ema = sum(prices[-period:]) / period
        else:
            ema = (prices[-1] - prev_ema) * multiplier + prev_ema

        return ema

    def _calculate_atr(
        self, highs: list[float], lows: list[float], closes: list[float]
    ) -> float:
        if len(highs) < 2:
            return 0.0

        true_ranges = []

        for i in range(1, len(highs)):
            high = highs[i]
            low = lows[i]
            prev_close = closes[i - 1]

            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)

        return sum(true_ranges) / len(true_ranges)

    def _calculate_rsi(self, prices: list[float], period: int) -> float:
        if len(prices) < period + 1:
            return 50.0

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        recent_deltas = deltas[-period:]

        gains = [d if d > 0 else 0 for d in recent_deltas]
        losses = [-d if d < 0 else 0 for d in recent_deltas]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))

        return rsi

    def _check_entry_signals(self, bar: Bar) -> None:
        close = float(bar.close)
        volume = float(bar.volume)

        if self.ema_slow == 0 or self.atr == 0:
            return

        is_bullish_trend = close > self.ema_slow
        is_bearish_trend = close < self.ema_slow

        is_near_ema_fast = abs(close - self.ema_fast) / close < 0.01

        volume_confirmed = volume >= self.volume_avg * self.config.volume_multiplier

        rsi_long_ok = self.rsi < self.config.rsi_overbought
        rsi_short_ok = self.rsi > self.config.rsi_oversold

        atr_pct = self.atr / close

        long_condition = (
            is_bullish_trend and is_near_ema_fast and volume_confirmed and rsi_long_ok
        )

        short_condition = (
            is_bearish_trend and is_near_ema_fast and volume_confirmed and rsi_short_ok
        )

        if long_condition:
            self._enter_long(bar)
        elif short_condition:
            self._enter_short(bar)

    def _enter_long(self, bar: Bar) -> None:
        close = float(bar.close)

        atr_sl = self.atr * self.config.atr_multiplier_sl
        atr_tp = self.atr * self.config.atr_multiplier_tp

        stop_loss = close - atr_sl
        take_profit = close + atr_tp

        instrument = self.cache.instrument(self.config.instrument_id)
        if instrument is None:
            self.log.error(f"Instrument {self.config.instrument_id} not found")
            return

        account = self.cache.account_for_venue(instrument.venue)
        if account is None:
            self.log.error(f"Account for venue {instrument.venue} not found")
            return

        balance = account.balance_total(instrument.quote_currency)
        position_value = balance * Decimal(str(self.config.position_size_pct))

        qty = instrument.make_qty(Decimal(str(position_value / close)))

        order = self.order_factory.market(
            instrument_id=instrument.id,
            order_side=OrderSide.BUY,
            quantity=qty,
        )

        self.submit_order(order)

        self.in_position = True
        self.entry_price = close
        self.stop_loss_price = stop_loss
        self.take_profit_price = take_profit

        self.log.info(
            f"LONG entry @ {close:.2f}, SL: {stop_loss:.2f}, TP: {take_profit:.2f}"
        )

    def _enter_short(self, bar: Bar) -> None:
        close = float(bar.close)

        atr_sl = self.atr * self.config.atr_multiplier_sl
        atr_tp = self.atr * self.config.atr_multiplier_tp

        stop_loss = close + atr_sl
        take_profit = close - atr_tp

        instrument = self.cache.instrument(self.config.instrument_id)
        if instrument is None:
            self.log.error(f"Instrument {self.config.instrument_id} not found")
            return

        account = self.cache.account_for_venue(instrument.venue)
        if account is None:
            self.log.error(f"Account for venue {instrument.venue} not found")
            return

        balance = account.balance_total(instrument.quote_currency)
        position_value = balance * Decimal(str(self.config.position_size_pct))

        qty = instrument.make_qty(Decimal(str(position_value / close)))

        order = self.order_factory.market(
            instrument_id=instrument.id,
            order_side=OrderSide.SELL,
            quantity=qty,
        )

        self.submit_order(order)

        self.in_position = True
        self.entry_price = close
        self.stop_loss_price = stop_loss
        self.take_profit_price = take_profit

        self.log.info(
            f"SHORT entry @ {close:.2f}, SL: {stop_loss:.2f}, TP: {take_profit:.2f}"
        )

    def _manage_position(self, bar: Bar) -> None:
        if (
            self.entry_price is None
            or self.stop_loss_price is None
            or self.take_profit_price is None
        ):
            return

        close = float(bar.close)

        if self.in_position:
            if close <= self.stop_loss_price or close >= self.take_profit_price:
                self._close_position(bar, reason="SL/TP")

            trend_changed = (
                self.entry_price < self.ema_slow and close > self.ema_slow
            ) or (self.entry_price > self.ema_slow and close < self.ema_slow)

            if trend_changed:
                self._close_position(bar, reason="Trend Change")

    def _close_position(self, bar: Bar, reason: str = "") -> None:
        instrument = self.cache.instrument(self.config.instrument_id)
        if instrument is None:
            return

        position = self.cache.position(instrument.id)
        if position is None or position.is_closed:
            self.in_position = False
            return

        current_qty = position.quantity

        if current_qty > 0:
            order = self.order_factory.market(
                instrument_id=instrument.id,
                order_side=OrderSide.SELL,
                quantity=current_qty,
            )
            self.submit_order(order)
            self.log.info(f"Closed LONG position @ {bar.close:.2f} - {reason}")
        elif current_qty < 0:
            order = self.order_factory.market(
                instrument_id=instrument.id,
                order_side=OrderSide.BUY,
                quantity=abs(current_qty),
            )
            self.submit_order(order)
            self.log.info(f"Closed SHORT position @ {bar.close:.2f} - {reason}")

        self.in_position = False
        self.entry_price = None
        self.stop_loss_price = None
        self.take_profit_price = None

    def on_stop(self) -> None:
        self.log.info("Trend Following Strategy stopped")
