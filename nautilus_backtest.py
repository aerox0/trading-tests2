#!/usr/bin/env python3
"""
Nautilus backtest runner for trend-following strategy on BTC/USDT 4H
"""

import time
from decimal import Decimal

import pandas as pd

from nautilus_trader.adapters.binance import BINANCE_VENUE
from nautilus_trader.backtest.config import BacktestEngineConfig
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import BTC, USDT
from nautilus_trader.model.enums import AccountType, BookType, OmsType
from nautilus_trader.model.identifiers import InstrumentId, TraderId
from nautilus_trader.model.instruments import CryptoPerpetual
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.test_kit.providers import TestInstrumentProvider

import sys

sys.path.insert(0, "/Users/aerox0/dev/trading-tests2")
from btc_data_fetcher import fetch_btc_data_4h, calculate_buy_and_hold_return
from nautilus_trend_strategy import TrendFollowingStrategy, TrendFollowingConfig


def create_btcusdt_instrument() -> CryptoPerpetual:
    """Create BTC/USDT instrument for backtesting"""
    return CryptoPerpetual(
        id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
        raw_symbol=InstrumentId.from_str("BTCUSDT-PERP.BINANCE").symbol,
        base_currency=BTC,
        quote_currency=USDT,
        settlement_currency=USDT,
        is_inverse=False,
        price_precision=2,
        price_increment=Price.from_str("0.01"),
        size_precision=8,
        size_increment=Quantity.from_str("0.00000001"),
        lot_size=Quantity.from_str("0.00000001"),
        max_quantity=Quantity.from_str("9000"),
        min_quantity=Quantity.from_str("0.00001"),
        ts_event=0,
        ts_init=0,
    )


def prepare_bar_data(df: pd.DataFrame) -> list:
    """
    Prepare bar data for Nautilus from DataFrame

    Args:
        df (pd.DataFrame): OHLCV data

    Returns:
        list: List of Bar objects or compatible data format
    """
    bars = []

    for idx, row in df.iterrows():
        bar_data = {
            "ts_event": int(idx.timestamp() * 1e9),
            "ts_init": int(idx.timestamp() * 1e9),
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": row["volume"],
        }
        bars.append(bar_data)

    return bars


def run_backtest(
    ema_fast_period=50,
    ema_slow_period=200,
    atr_period=14,
    atr_multiplier_sl=0.5,
    atr_multiplier_tp=2.0,
    rsi_period=14,
    volume_multiplier=1.2,
    position_size_pct=0.5,
    initial_capital=10000.0,
):
    """
    Run Nautilus backtest with given parameters

    Returns:
        dict: Backtest results
    """
    print(f"\n{'=' * 80}")
    print(f"RUNNING NAUTILUS BACKTEST")
    print(f"{'=' * 80}")
    print(f"Strategy Parameters:")
    print(f"  EMA Fast: {ema_fast_period}, EMA Slow: {ema_slow_period}")
    print(
        f"  ATR Period: {atr_period}, SL Multiplier: {atr_multiplier_sl}, TP Multiplier: {atr_multiplier_tp}"
    )
    print(f"  RSI Period: {rsi_period}")
    print(f"  Volume Multiplier: {volume_multiplier}")
    print(f"  Position Size: {position_size_pct * 100:.0f}%")
    print(f"  Initial Capital: ${initial_capital:,.2f}")
    print(f"{'=' * 80}\n")

    config = BacktestEngineConfig(
        trader_id=TraderId("BACKTESTER-001"),
        logging=LoggingConfig(
            log_level="WARNING",
            log_colors=True,
            use_pyo3=False,
        ),
    )

    engine = BacktestEngine(config=config)

    instrument = create_btcusdt_instrument()
    engine.add_instrument(instrument)

    engine.add_venue(
        venue=BINANCE_VENUE,
        oms_type=OmsType.NETTING,
        book_type=BookType.L1_MBP,
        account_type=AccountType.CASH,
        base_currency=USDT,
        starting_balances=[Money(initial_capital, USDT)],
        trade_execution=True,
    )

    df = fetch_btc_data_4h(symbol="BTC/USDT", period_days=730)

    from nautilus_trader.model.data import Bar, BarType
    from nautilus_trader.persistence.wranglers import BarDataWrangler

    bar_type = BarType.from_str("BTCUSDT.BINANCE-240-MINUTE-LAST-EXTERNAL")

    wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)

    bars = []
    for idx, row in df.iterrows():
        bar = wrangler.process_bar(
            {
                "ts_event": int(idx.timestamp() * 1e9),
                "ts_init": int(idx.timestamp() * 1e9),
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"],
                "ts_event": int(idx.timestamp() * 1e9),
            }
        )
        if bar:
            bars.append(bar)

    if not bars:
        raise ValueError("No bars generated from data")

    engine.add_data(bars)

    strategy_config = TrendFollowingConfig(
        instrument_id=instrument.id,
        bar_type=bar_type,
        ema_fast_period=ema_fast_period,
        ema_slow_period=ema_slow_period,
        atr_period=atr_period,
        atr_multiplier_sl=atr_multiplier_sl,
        atr_multiplier_tp=atr_multiplier_tp,
        rsi_period=rsi_period,
        volume_multiplier=volume_multiplier,
        position_size_pct=position_size_pct,
    )

    strategy = TrendFollowingStrategy(config=strategy_config)
    engine.add_strategy(strategy=strategy)

    time.sleep(0.5)

    print("Running backtest...")
    result = engine.run()

    print("\nGenerating reports...")

    account_report = engine.trader.generate_account_report(BINANCE_VENUE)
    fills_report = engine.trader.generate_order_fills_report()
    positions_report = engine.trader.generate_positions_report()

    print("\n" + "=" * 80)
    print("ACCOUNT REPORT")
    print("=" * 80)
    print(account_report)

    print("\n" + "=" * 80)
    print("POSITIONS REPORT")
    print("=" * 80)
    print(positions_report)

    print("\n" + "=" * 80)
    print("ORDER FILLS REPORT")
    print("=" * 80)
    print(fills_report)

    ba_h_metrics = calculate_buy_and_hold_return(df, initial_capital=initial_capital)

    strategy_return = ba_h_metrics["total_return_pct"]

    print("\n" + "=" * 80)
    print("COMPARISON WITH BUY AND HOLD")
    print("=" * 80)
    print(f"Strategy Return: {strategy_return:+.2f}%")
    print(f"Buy & Hold Return: {ba_h_metrics['total_return_pct']:+.2f}%")
    print(f"Difference: {strategy_return - ba_h_metrics['total_return_pct']:+.2f}%")
    print("=" * 80)

    engine.reset()
    engine.dispose()

    return {
        "strategy_return": strategy_return,
        "buy_and_hold_return": ba_h_metrics["total_return_pct"],
        "difference": strategy_return - ba_h_metrics["total_return_pct"],
        "ba_h_metrics": ba_h_metrics,
    }


def grid_search():
    """
    Perform grid search for optimal parameters
    """
    print("\n" + "=" * 80)
    print("GRID SEARCH FOR OPTIMAL PARAMETERS")
    print("=" * 80)

    param_grid = {
        "ema_fast_period": [34, 50, 55],
        "ema_slow_period": [144, 200, 252],
        "atr_period": [14, 20],
        "atr_multiplier_sl": [0.4, 0.5, 0.6],
        "atr_multiplier_tp": [1.5, 2.0, 2.5],
        "volume_multiplier": [1.0, 1.2, 1.5],
        "position_size_pct": [0.3, 0.5, 0.7],
    }

    best_result = None
    best_params = None
    ba_h_return = None

    total_iterations = (
        len(param_grid["ema_fast_period"])
        * len(param_grid["ema_slow_period"])
        * len(param_grid["atr_period"])
        * len(param_grid["atr_multiplier_sl"])
        * len(param_grid["atr_multiplier_tp"])
        * len(param_grid["volume_multiplier"])
        * len(param_grid["position_size_pct"])
    )

    print(f"Total iterations: {total_iterations}")
    print("This may take a while...\n")

    iteration = 0

    for ema_fast in param_grid["ema_fast_period"]:
        for ema_slow in param_grid["ema_slow_period"]:
            if ema_fast >= ema_slow:
                continue

            for atr_p in param_grid["atr_period"]:
                for atr_sl in param_grid["atr_multiplier_sl"]:
                    for atr_tp in param_grid["atr_multiplier_tp"]:
                        for vol_mult in param_grid["volume_multiplier"]:
                            for pos_size in param_grid["position_size_pct"]:
                                iteration += 1
                                print(f"\nIteration {iteration}/{total_iterations}")
                                print(
                                    f"Testing: EMA({ema_fast},{ema_slow}) "
                                    f"ATR({atr_p}) SL({atr_sl}) TP({atr_tp}) "
                                    f"Vol({vol_mult}) Size({pos_size * 100:.0f}%)"
                                )

                                try:
                                    result = run_backtest(
                                        ema_fast_period=ema_fast,
                                        ema_slow_period=ema_slow,
                                        atr_period=atr_p,
                                        atr_multiplier_sl=atr_sl,
                                        atr_multiplier_tp=atr_tp,
                                        volume_multiplier=vol_mult,
                                        position_size_pct=pos_size,
                                    )

                                    if ba_h_return is None:
                                        ba_h_return = result["buy_and_hold_return"]

                                    strategy_return = result["strategy_return"]
                                    difference = result["difference"]

                                    print(
                                        f"Result: {strategy_return:+.2f}% "
                                        f"(vs BaH: {ba_h_return:+.2f}%, "
                                        f"Diff: {difference:+.2f}%)"
                                    )

                                    if (
                                        best_result is None
                                        or difference > best_result["difference"]
                                    ):
                                        best_result = result
                                        best_params = {
                                            "ema_fast_period": ema_fast,
                                            "ema_slow_period": ema_slow,
                                            "atr_period": atr_p,
                                            "atr_multiplier_sl": atr_sl,
                                            "atr_multiplier_tp": atr_tp,
                                            "volume_multiplier": vol_mult,
                                            "position_size_pct": pos_size,
                                        }
                                        print(f"*** NEW BEST RESULT ***")

                                except Exception as e:
                                    print(f"Error: {e}")
                                    continue

    print("\n" + "=" * 80)
    print("GRID SEARCH COMPLETE")
    print("=" * 80)
    if best_params is not None:
        print("\nBest Parameters:")
        for k, v in best_params.items():
            print(f"  {k}: {v}")

    if best_result is not None:
        print(f"\nBest Result:")
        print(f"  Strategy Return: {best_result['strategy_return']:+.2f}%")
        print(f"  Buy & Hold Return: {best_result['buy_and_hold_return']:+.2f}%")
        print(f"  Difference: {best_result['difference']:+.2f}%")
    print("=" * 80)

    return best_result, best_params


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "grid":
        grid_search()
    else:
        result = run_backtest(
            ema_fast_period=50,
            ema_slow_period=200,
            atr_period=14,
            atr_multiplier_sl=0.5,
            atr_multiplier_tp=2.0,
            rsi_period=14,
            volume_multiplier=1.2,
            position_size_pct=0.5,
            initial_capital=10000.0,
        )
        print(result)
