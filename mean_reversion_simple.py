import ccxt
import pandas as pd
import numpy as np
from datetime import datetime

print("=" * 80)
print("MEAN REVERSION AT EXTREMES - BACKTESTING ON 4H TIMEFRAME")
print("=" * 80)


def fetch_data(symbol="BTC/USDT", timeframe="4h", days=730):
    print(f"\nFetching {days} days of {timeframe} candles for {symbol}...")
    exchange = ccxt.binance()

    since = exchange.milliseconds() - (days * 24 * 60 * 60 * 1000)
    all_ohlcv = []

    while True:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
        if len(ohlcv) == 0:
            break
        all_ohlcv.extend(ohlcv)
        since = ohlcv[-1][0] + 1
        print(f"  Fetched {len(ohlcv)} candles, total: {len(all_ohlcv)}")
        if len(ohlcv) < 1000:
            break

    df = pd.DataFrame(
        all_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df = df[~df.index.duplicated(keep="first")]
    df = df.sort_index()

    print(f"\nData Summary:")
    print(f"  Period: {df.index[0]} to {df.index[-1]}")
    print(f"  Total Candles: {len(df)}")
    print(f"  Price Range: ${df['close'].min():,.2f} to ${df['close'].max():,.2f}")

    return df


def calculate_bollinger_bands(df, period=20, devfactor=2.0, trend_period=50):
    df["ma"] = df["close"].rolling(window=period).mean()
    df["std"] = df["close"].rolling(window=period).std()
    df["upper_band"] = df["ma"] + (df["std"] * devfactor)
    df["lower_band"] = df["ma"] - (df["std"] * devfactor)
    df["trend_ma"] = df["close"].rolling(window=trend_period).mean()
    df["distance_from_ma"] = (df["close"] - df["ma"]) / df["ma"] * 100
    return df


def backtest_strategy(df, config):
    bb_period = config["bb_period"]
    bb_devfactor = config["bb_devfactor"]
    position_size_pct = config["position_size_pct"]
    stop_loss_pct = config["stop_loss_pct"]
    max_hold_bars = config["max_hold_bars"]
    commission = config.get("commission", 0.0002)
    use_trend_filter = config.get("use_trend_filter", True)
    allow_shorts = config.get("allow_shorts", False)

    df = calculate_bollinger_bands(df.copy(), bb_period, bb_devfactor, 50)

    cash = 10000.0
    position_btc = 0.0
    entry_price = None
    entry_type = None
    hold_bars = 0

    trades = []

    for i in range(len(df)):
        if pd.isna(df["upper_band"].iloc[i]):
            continue

        current_price = float(df["close"].iloc[i])
        upper_band = float(df["upper_band"].iloc[i])
        lower_band = float(df["lower_band"].iloc[i])
        ma = float(df["ma"].iloc[i])
        trend_ma = float(df["trend_ma"].iloc[i])

        if position_btc == 0:
            if use_trend_filter:
                in_uptrend = current_price > trend_ma
                in_downtrend = current_price < trend_ma
            else:
                in_uptrend = True
                in_downtrend = True

            if allow_shorts and current_price > upper_band and in_downtrend:
                position_value_usdt = cash * position_size_pct
                position_btc = position_value_usdt / current_price
                cash -= position_value_usdt
                entry_price = current_price
                entry_type = "short"
                hold_bars = 0

                commission_cost = position_value_usdt * commission
                cash -= commission_cost

                trades.append(
                    {
                        "entry_time": df.index[i],
                        "entry_price": current_price,
                        "type": "short",
                        "size": position_btc,
                    }
                )

                print(
                    f"[{df.index[i]}] SHORT ENTRY: ${current_price:.2f} above upper band ${upper_band:.2f}"
                )

            elif current_price < lower_band and in_uptrend:
                position_value_usdt = cash * position_size_pct
                position_btc = position_value_usdt / current_price
                cash -= position_value_usdt
                entry_price = current_price
                entry_type = "long"
                hold_bars = 0

                commission_cost = position_value_usdt * commission
                cash -= commission_cost

                trades.append(
                    {
                        "entry_time": df.index[i],
                        "entry_price": current_price,
                        "type": "long",
                        "size": position_btc,
                    }
                )

                print(
                    f"[{df.index[i]}] LONG ENTRY: ${current_price:.2f} below lower band ${lower_band:.2f}"
                )

        else:
            hold_bars += 1
            exit_trade = False
            exit_reason = ""

            stop_loss_price_long = entry_price * (1 - stop_loss_pct)
            stop_loss_price_short = entry_price * (1 + stop_loss_pct)
            target_price = ma

            if entry_type == "long":
                if current_price <= stop_loss_price_long:
                    exit_trade = True
                    exit_reason = "STOP LOSS"
                elif current_price >= target_price:
                    exit_trade = True
                    exit_reason = "TARGET"
                elif hold_bars >= max_hold_bars:
                    exit_trade = True
                    exit_reason = "MAX HOLD"
            else:
                if current_price >= stop_loss_price_short:
                    exit_trade = True
                    exit_reason = "STOP LOSS"
                elif current_price <= target_price:
                    exit_trade = True
                    exit_reason = "TARGET"
                elif hold_bars >= max_hold_bars:
                    exit_trade = True
                    exit_reason = "MAX HOLD"

            if exit_trade:
                if entry_type == "long":
                    exit_value = position_btc * current_price
                    commission_cost = exit_value * commission
                    cash += exit_value - commission_cost
                    pnl_pct = (current_price - entry_price) / entry_price * 100
                    print(
                        f"[{df.index[i]}] LONG EXIT ({exit_reason}): Hold {hold_bars} bars, ${current_price:.2f}, P/L: {pnl_pct:.2f}%"
                    )
                else:
                    pnl_pct = (entry_price - current_price) / entry_price * 100
                    exit_value = abs(position_btc) * entry_price * (1 + pnl_pct / 100)
                    commission_cost = exit_value * commission
                    cash += exit_value - commission_cost
                    print(
                        f"[{df.index[i]}] SHORT EXIT ({exit_reason}): Hold {hold_bars} bars, ${current_price:.2f}, P/L: {pnl_pct:.2f}%"
                    )

                trades[-1]["exit_time"] = df.index[i]
                trades[-1]["exit_price"] = current_price
                trades[-1]["exit_reason"] = exit_reason
                trades[-1]["hold_bars"] = hold_bars
                trades[-1]["pnl_pct"] = pnl_pct

                position_btc = 0
                entry_price = None
                entry_type = None

    if position_btc != 0:
        final_price = float(df["close"].iloc[-1])
        if entry_type == "long":
            exit_value = position_btc * final_price
            commission_cost = exit_value * commission
            cash += exit_value - commission_cost
            pnl_pct = (final_price - entry_price) / entry_price * 100
        else:
            pnl_pct = (entry_price - final_price) / entry_price * 100
            exit_value = abs(position_btc) * entry_price * (1 + pnl_pct / 100)
            commission_cost = exit_value * commission
            cash += exit_value - commission_cost

        trades[-1]["exit_time"] = df.index[-1]
        trades[-1]["exit_price"] = final_price
        trades[-1]["exit_reason"] = "FORCED CLOSE"
        trades[-1]["hold_bars"] = hold_bars
        trades[-1]["pnl_pct"] = pnl_pct

        print(f"[{df.index[-1]}] FORCED CLOSE: ${final_price:.2f}, P/L: {pnl_pct:.2f}%")

    return trades, cash


def calculate_metrics(trades, initial_cash=10000):
    if not trades:
        return {
            "total_trades": 0,
            "won_trades": 0,
            "lost_trades": 0,
            "win_rate": 0,
            "total_return": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "profit_factor": 0,
        }

    total_trades = len(trades)
    won_trades = sum(1 for t in trades if t["pnl_pct"] > 0)
    lost_trades = total_trades - won_trades

    win_rate = (won_trades / total_trades) * 100

    wins = [t["pnl_pct"] for t in trades if t["pnl_pct"] > 0]
    losses = [t["pnl_pct"] for t in trades if t["pnl_pct"] < 0]

    avg_win = np.mean(wins) if wins else 0
    avg_loss = np.mean(losses) if losses else 0

    total_win_pct = sum(wins)
    total_loss_pct = sum(losses)
    profit_factor = (
        abs(total_win_pct / total_loss_pct) if total_loss_pct != 0 else float("inf")
    )

    return {
        "total_trades": total_trades,
        "won_trades": won_trades,
        "lost_trades": lost_trades,
        "win_rate": win_rate,
        "total_return_pct": sum(t["pnl_pct"] for t in trades),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
    }


def print_results(config, metrics, final_cash, initial_cash=10000):
    print(f"\n{'=' * 80}")
    print(f"RESULTS FOR: {config['name']}")
    print(f"{'=' * 80}")
    print(f"  BB Period: {config['bb_period']}")
    print(f"  BB Dev Factor: {config['bb_devfactor']}")
    print(f"  Position Size: {config['position_size_pct'] * 100}%")
    print(f"  Stop Loss: {config['stop_loss_pct'] * 100}%")
    print(f"  Max Hold Bars: {config['max_hold_bars']}")
    print(f"  Trend Filter: {config.get('use_trend_filter', False)}")
    print(f"  Allow Shorts: {config.get('allow_shorts', False)}")
    print()
    print(f"  Total Return: {final_cash / initial_cash * 100 - 100:+.2f}%")
    print(f"  Final Cash: ${final_cash:,.2f}")
    print(f"  Total Trades: {metrics['total_trades']}")
    print(f"  Win Rate: {metrics['win_rate']:.1f}%")
    print(f"  Won Trades: {metrics['won_trades']}")
    print(f"  Lost Trades: {metrics['lost_trades']}")
    print(f"  Average Win: {metrics['avg_win']:.2f}%")
    print(f"  Average Loss: {metrics['avg_loss']:.2f}%")
    print(f"  Profit Factor: {metrics['profit_factor']:.2f}")


def main():
    try:
        df = fetch_data(symbol="BTC/USDT", timeframe="4h", days=730)

        strategy_configs = [
            {
                "name": "Config A (Long only, 1.8 std, 1.5% SL, trend filter)",
                "bb_period": 20,
                "bb_devfactor": 1.8,
                "position_size_pct": 0.20,
                "stop_loss_pct": 0.015,
                "max_hold_bars": 20,
                "use_trend_filter": True,
                "allow_shorts": False,
                "commission": 0.0002,
            },
            {
                "name": "Config B (Long only, 2.0 std, 1.8% SL, trend filter)",
                "bb_period": 20,
                "bb_devfactor": 2.0,
                "position_size_pct": 0.20,
                "stop_loss_pct": 0.018,
                "max_hold_bars": 15,
                "use_trend_filter": True,
                "allow_shorts": False,
                "commission": 0.0002,
            },
            {
                "name": "Config C (Long only, 2.2 std, 2.0% SL, no trend)",
                "bb_period": 20,
                "bb_devfactor": 2.2,
                "position_size_pct": 0.25,
                "stop_loss_pct": 0.02,
                "max_hold_bars": 12,
                "use_trend_filter": False,
                "allow_shorts": False,
                "commission": 0.0002,
            },
            {
                "name": "Config D (Long only, 2.5 std, 2.2% SL, no trend)",
                "bb_period": 20,
                "bb_devfactor": 2.5,
                "position_size_pct": 0.25,
                "stop_loss_pct": 0.022,
                "max_hold_bars": 10,
                "use_trend_filter": False,
                "allow_shorts": False,
                "commission": 0.0002,
            },
            {
                "name": "Config E (Both sides, 2.0 std, 1.8% SL, no filter)",
                "bb_period": 20,
                "bb_devfactor": 2.0,
                "position_size_pct": 0.25,
                "stop_loss_pct": 0.018,
                "max_hold_bars": 12,
                "use_trend_filter": False,
                "allow_shorts": True,
                "commission": 0.0002,
            },
        ]

        print(f"\n{'=' * 80}")
        print("Testing enhanced Mean Reversion strategies to achieve +200% return")
        print(f"{'=' * 80}\n")

        best_results = None
        best_config_name = None
        best_final_cash = None

        for config in strategy_configs:
            print(f"\n{'=' * 80}")
            print(f"Running {config['name']}")
            print(f"{'=' * 80}")

            trades, final_cash = backtest_strategy(df, config)
            metrics = calculate_metrics(trades, initial_cash=10000)
            print_results(config, metrics, final_cash, initial_cash=10000)

            if best_results is None or final_cash > best_final_cash:
                best_results = metrics
                best_config_name = config["name"]
                best_final_cash = final_cash

        print(f"\n{'=' * 80}")
        print("SUMMARY")
        print(f"{'=' * 80}")
        print(f"Best configuration: {best_config_name}")
        print(f"Win rate: {best_results['win_rate']:.1f}%")
        print(f"Total return: {best_final_cash / 10000 * 100 - 100:+.2f}%")
        print(f"Total trades: {best_results['total_trades']}")

        if best_final_cash / 10000 * 100 - 100 >= 100:
            print(f"Status: EXCELLENT - Over 100% return!")
        elif best_final_cash / 10000 * 100 - 100 >= 50:
            print(f"Status: GOOD - Strong performance")
        elif best_final_cash / 10000 * 100 - 100 >= 0:
            print(f"Status: POSITIVE - Profitable")
        else:
            print(f"Status: NEGATIVE - Need more tuning")

        print(f"{'=' * 80}\n")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
