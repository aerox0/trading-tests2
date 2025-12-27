#!/usr/bin/env python3
"""
Time-Based Strategy Backtest for BTCUSDT
Compares three versions of time-based edge strategy with buy-and-hold baseline
Uses Backtrader framework
"""

import backtrader as bt
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def fetch_crypto_data(symbol="BTC/USDT", timeframe="1h", period_days=730):
    """Fetch historical data from Binance"""
    exchange = ccxt.binance()

    end_time = int(datetime.now().timestamp() * 1000)
    start_time = end_time - (period_days * 24 * 60 * 60 * 1000)

    all_ohlcv = []
    current_time = start_time

    while current_time < end_time:
        limit = 1000
        ohlcv = exchange.fetch_ohlcv(
            symbol, timeframe=timeframe, since=current_time, limit=limit
        )

        if len(ohlcv) == 0:
            break

        all_ohlcv.extend(ohlcv)
        current_time = ohlcv[-1][0] + 1

    if len(all_ohlcv) == 0:
        raise ValueError(f"No data fetched from Binance for {symbol}")

    df = pd.DataFrame(
        all_ohlcv, columns=["datetime", "open", "high", "low", "close", "volume"]
    )
    df["datetime"] = pd.to_datetime(df["datetime"], unit="ms")
    df.set_index("datetime", inplace=True)

    return df


class TimeBasedStrategyA(bt.Strategy):
    """Version A: Pure Analytics-Based
    Entry: Buy at market open of hours 17, 21, 22 UTC
    Exit: Close at end of that same hour (next candle open)
    No filters, no stops, no targets
    """

    params = (
        ("trading_hours", [17, 21, 22]),
        ("position_size", 0.05),
    )

    def __init__(self):
        self.entry_hour = None
        self.trades = []
        self.portfolio_values = []

    def next(self):
        # Track portfolio value
        self.portfolio_values.append(self.broker.getvalue())

        current_dt = self.data.datetime.datetime(0)
        current_hour = current_dt.hour

        # Entry: Buy at market open of trading hours
        if not self.position and current_hour in self.params.trading_hours:
            # Only buy at candle close, not during the hour
            if len(self.data) >= 2:
                self.entry_hour = current_hour
                size = (
                    self.broker.getvalue()
                    * self.params.position_size
                    / self.data.close[0]
                )
                self.buy(size=size)

        # Exit: Close position at start of next hour (candle open)
        elif self.position:
            if current_hour != self.entry_hour:
                self.close()

    def notify_trade(self, trade):
        """Track completed trades"""
        if trade.isclosed:
            self.trades.append(trade)


class TimeBasedStrategyB(bt.Strategy):
    """Version B: Optimized Risk/Reward
    Entry: Buy at market open of hours 17, 21, 22 UTC
    Exit: Take profit at +0.8%, Stop loss at -0.5%, OR end of hour
    """

    params = (
        ("trading_hours", [17, 21, 22]),
        ("position_size", 0.05),
        ("profit_target", 0.008),
        ("stop_loss", 0.005),
    )

    def __init__(self):
        self.entry_hour = None
        self.entry_price = None
        self.trades = []
        self.portfolio_values = []

    def next(self):
        # Track portfolio value
        self.portfolio_values.append(self.broker.getvalue())

        current_dt = self.data.datetime.datetime(0)
        current_hour = current_dt.hour

        # Entry: Buy at market open of trading hours
        if not self.position and current_hour in self.params.trading_hours:
            if len(self.data) >= 2:
                self.entry_hour = current_hour
                self.entry_price = self.data.close[0]
                size = (
                    self.broker.getvalue()
                    * self.params.position_size
                    / self.data.close[0]
                )

                # Calculate target and stop prices
                target_price = self.entry_price * (1 + self.params.profit_target)
                stop_price = self.entry_price * (1 - self.params.stop_loss)

                # Buy and set target/stop
                self.buy(size=size)
                self.sell(size=size, exectype=bt.Order.Limit, price=target_price)

        # Exit conditions
        elif self.position:
            # Check stop loss
            if self.data.low[0] <= self.entry_price * (1 - self.params.stop_loss):
                self.close()

            # Check if hour changed
            elif current_hour != self.entry_hour:
                self.close()

    def notify_trade(self, trade):
        """Track completed trades"""
        if trade.isclosed:
            self.trades.append(trade)


class TimeBasedStrategyC(bt.Strategy):
    """Version C: Multi-Filter (TradingView-style)
    Entry: Hours 17, 21, 22 + previous green + volume filter + trend filter
    Exit: Target, stop, or hour end
    """

    params = (
        ("trading_hours", [17, 21, 22]),
        ("position_size", 0.05),
        ("profit_target", 0.008),
        ("stop_loss", 0.005),
        ("volume_period", 20),
        ("sma_period", 5),
        ("warmup_period", 50),
    )

    def __init__(self):
        self.entry_hour = None
        self.entry_price = None
        self.trades = []
        self.portfolio_values = []

        # Indicators
        self.sma = bt.indicators.SMA(self.data.close, period=self.params.sma_period)
        self.sma_volume = bt.indicators.SMA(
            self.data.volume, period=self.params.volume_period
        )

    def next(self):
        # Warmup period
        if len(self.data) < self.params.warmup_period:
            return

        # Track portfolio value
        self.portfolio_values.append(self.broker.getvalue())

        current_dt = self.data.datetime.datetime(0)
        current_hour = current_dt.hour

        # Update filters based on previous candle
        if len(self.data) >= 2:
            self.prev_candle_green = self.data.close[-1] > self.data.open[-1]
            self.prev_high_volume = self.data.volume[-1] > self.sma_volume[-1]
        else:
            self.prev_candle_green = False
            self.prev_high_volume = False

        # Entry conditions
        if (
            not self.position
            and current_hour in self.params.trading_hours
            and self.prev_candle_green
            and self.prev_high_volume
            and self.data.close[0] > self.sma[0]
        ):
            self.entry_hour = current_hour
            self.entry_price = self.data.close[0]
            size = (
                self.broker.getvalue() * self.params.position_size / self.data.close[0]
            )

            # Calculate target and stop prices
            target_price = self.entry_price * (1 + self.params.profit_target)
            stop_price = self.entry_price * (1 - self.params.stop_loss)

            # Buy and set target/stop
            self.buy(size=size)
            self.sell(size=size, exectype=bt.Order.Limit, price=target_price)

        # Exit conditions
        elif self.position:
            # Check stop loss
            if self.data.low[0] <= self.entry_price * (1 - self.params.stop_loss):
                self.close()

            # Check if hour changed
            elif current_hour != self.entry_hour:
                self.close()

    def notify_trade(self, trade):
        """Track completed trades"""
        if trade.isclosed:
            self.trades.append(trade)


class BuyAndHold(bt.Strategy):
    """Buy-and-Hold Baseline
    Entry: Buy at start
    Exit: Sell at end of backtest
    """

    def __init__(self):
        self.bought = False
        self.trades = []
        self.portfolio_values = []

    def next(self):
        # Track portfolio value
        self.portfolio_values.append(self.broker.getvalue())

        if not self.bought and len(self.data) >= 2:
            size = self.broker.getvalue() / self.data.close[0]
            self.buy(size=size)
            self.bought = True

    def notify_trade(self, trade):
        """Track completed trades"""
        if trade.isclosed:
            self.trades.append(trade)


def calculate_sharpe(returns, risk_free_rate=0.02):
    """Calculate annualized Sharpe ratio"""
    if len(returns) < 2 or np.std(returns) == 0:
        return 0.0

    returns_array = np.array(returns)
    excess_returns = returns_array - risk_free_rate / 252
    sharpe = np.mean(excess_returns) / np.std(excess_returns)
    sharpe_annualized = sharpe * np.sqrt(252)

    return sharpe_annualized


def calculate_max_drawdown(equity_curve):
    """Calculate maximum drawdown"""
    peak = equity_curve[0]
    max_dd = 0.0

    for value in equity_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak * 100
        if dd > max_dd:
            max_dd = dd

    return max_dd


def calculate_strategy_results(strategy):
    """Calculate detailed metrics for a strategy"""
    trades = strategy.trades

    total_trades = len(trades)
    wins = [t for t in trades if hasattr(t, "pnlcomm") and t.pnlcomm > 0]
    losses = [t for t in trades if hasattr(t, "pnlcomm") and t.pnlcomm < 0]

    win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0.0
    avg_win = np.mean([t.pnlcomm for t in wins]) if wins else 0.0
    avg_loss = np.mean([t.pnlcomm for t in losses]) if losses else 0.0
    gross_profit = sum([t.pnlcomm for t in wins])
    gross_loss = abs(sum([t.pnlcomm for t in losses]))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

    # Calculate returns over time
    portfolio_values = strategy.portfolio_values
    returns = []

    # Simple returns calculation
    for i in range(1, len(portfolio_values)):
        prev_val = portfolio_values[i - 1]
        curr_val = portfolio_values[i]
        if prev_val > 0:
            returns.append((curr_val - prev_val) / prev_val)

    sharpe = calculate_sharpe(returns) if returns else 0.0

    # Calculate trade durations
    durations = []
    for trade in trades:
        if hasattr(trade, "dtopen") and hasattr(trade, "dtclose"):
            # Convert datetime difference to hours
            try:
                duration = (trade.dtclose - trade.dtopen).total_seconds() / 3600
                durations.append(duration)
            except AttributeError:
                # If dtclose/dtopen are not datetime objects, skip duration calculation
                pass

    avg_duration = np.mean(durations) if durations else 0.0

    return {
        "total_trades": total_trades,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "sharpe_ratio": sharpe,
        "avg_duration": avg_duration,
    }


def run_backtest(timeframe="1h"):
    """Run backtest for all strategies on given timeframe"""
    print(f"\n{'=' * 80}")
    print(f"TIME-BASED STRATEGY BACKTEST - BTC/USDT ({timeframe.upper()})")
    print(f"{'=' * 80}")

    # Fetch data
    print(f"\nFetching data...")
    df = fetch_crypto_data(symbol="BTC/USDT", timeframe=timeframe, period_days=730)

    print(f"Data Period: {df.index.min()} to {df.index.max()}")
    print(f"Total Candles: {len(df)}")

    # Prepare data for backtrader
    data = bt.feeds.PandasData(
        dataname=df,
        datetime=None,
        open="open",
        high="high",
        low="low",
        close="close",
        volume="volume",
        openinterest=-1,
    )

    results = {}

    # Version A: Pure Analytics-Based
    print(f"\nRunning Version A: Pure Analytics-Based...")
    cerebro_a = bt.Cerebro()
    cerebro_a.adddata(data)
    cerebro_a.addstrategy(TimeBasedStrategyA)
    cerebro_a.broker.setcash(10000.0)
    cerebro_a.broker.setcommission(commission=0.0002)

    start_value_a = cerebro_a.broker.getvalue()
    strategies_a = cerebro_a.run()
    end_value_a = cerebro_a.broker.getvalue()
    total_return_a = (end_value_a - start_value_a) / start_value_a * 100

    metrics_a = calculate_strategy_results(strategies_a[0])

    # Version B: Optimized Risk/Reward
    print(f"Running Version B: Optimized Risk/Reward...")
    cerebro_b = bt.Cerebro()
    cerebro_b.adddata(data)
    cerebro_b.addstrategy(TimeBasedStrategyB)
    cerebro_b.broker.setcash(10000.0)
    cerebro_b.broker.setcommission(commission=0.0002)

    start_value_b = cerebro_b.broker.getvalue()
    strategies_b = cerebro_b.run()
    end_value_b = cerebro_b.broker.getvalue()
    total_return_b = (end_value_b - start_value_b) / start_value_b * 100

    metrics_b = calculate_strategy_results(strategies_b[0])

    # Version C: Multi-Filter
    print(f"Running Version C: Multi-Filter...")
    cerebro_c = bt.Cerebro()
    cerebro_c.adddata(data)
    cerebro_c.addstrategy(TimeBasedStrategyC)
    cerebro_c.broker.setcash(10000.0)
    cerebro_c.broker.setcommission(commission=0.0002)

    start_value_c = cerebro_c.broker.getvalue()
    strategies_c = cerebro_c.run()
    end_value_c = cerebro_c.broker.getvalue()
    total_return_c = (end_value_c - start_value_c) / start_value_c * 100

    metrics_c = calculate_strategy_results(strategies_c[0])

    # Buy-and-Hold Baseline
    print(f"Running Buy-and-Hold Baseline...")
    cerebro_bh = bt.Cerebro()
    cerebro_bh.adddata(data)
    cerebro_bh.addstrategy(BuyAndHold)
    cerebro_bh.broker.setcash(10000.0)
    cerebro_bh.broker.setcommission(commission=0.0002)

    start_value_bh = cerebro_bh.broker.getvalue()
    strategies_bh = cerebro_bh.run()
    end_value_bh = cerebro_bh.broker.getvalue()
    total_return_bh = (end_value_bh - start_value_bh) / start_value_bh * 100

    # Calculate max drawdown and Sharpe for buy-and-hold
    equity_bh = strategies_bh[0].portfolio_values
    max_dd_bh = calculate_max_drawdown(equity_bh)
    sharpe_bh = calculate_sharpe([(end_value_bh - start_value_bh) / start_value_bh])

    # Display results
    print(f"\nInitial Capital: $10,000.00")
    print(f"Commission: 0.02% per trade")
    print(f"\n{'=' * 80}")

    print(f"\n--- VERSION A: Pure Analytics-Based ---")
    print(f"Final Portfolio Value: ${end_value_a:,.2f}")
    print(f"Total Return: {total_return_a:+.2f}%")
    print(f"Win Rate: {metrics_a['win_rate']:.1f}%")
    print(f"Total Trades: {metrics_a['total_trades']}")
    print(f"Average Win: ${metrics_a['avg_win']:+.2f}")
    print(f"Average Loss: ${metrics_a['avg_loss']:+.2f}")
    print(f"Profit Factor: {metrics_a['profit_factor']:.2f}")
    print(f"Sharpe Ratio: {metrics_a['sharpe_ratio']:.2f}")
    print(f"Average Trade Duration: {metrics_a['avg_duration']:.1f} hours")

    print(f"\n--- VERSION B: Optimized Risk/Reward ---")
    print(f"Final Portfolio Value: ${end_value_b:,.2f}")
    print(f"Total Return: {total_return_b:+.2f}%")
    print(f"Win Rate: {metrics_b['win_rate']:.1f}%")
    print(f"Total Trades: {metrics_b['total_trades']}")
    print(f"Average Win: ${metrics_b['avg_win']:+.2f}")
    print(f"Average Loss: ${metrics_b['avg_loss']:+.2f}")
    print(f"Profit Factor: {metrics_b['profit_factor']:.2f}")
    print(f"Sharpe Ratio: {metrics_b['sharpe_ratio']:.2f}")
    print(f"Average Trade Duration: {metrics_b['avg_duration']:.1f} hours")

    print(f"\n--- VERSION C: Multi-Filter (TradingView-style) ---")
    print(f"Final Portfolio Value: ${end_value_c:,.2f}")
    print(f"Total Return: {total_return_c:+.2f}%")
    print(f"Win Rate: {metrics_c['win_rate']:.1f}%")
    print(f"Total Trades: {metrics_c['total_trades']}")
    print(f"Average Win: ${metrics_c['avg_win']:+.2f}")
    print(f"Average Loss: ${metrics_c['avg_loss']:+.2f}")
    print(f"Profit Factor: {metrics_c['profit_factor']:.2f}")
    print(f"Sharpe Ratio: {metrics_c['sharpe_ratio']:.2f}")
    print(f"Average Trade Duration: {metrics_c['avg_duration']:.1f} hours")

    print(f"\n--- BUY-AND-HOLD BASELINE ---")
    print(f"Final Portfolio Value: ${end_value_bh:,.2f}")
    print(f"Total Return: {total_return_bh:+.2f}%")
    print(f"Max Drawdown: {max_dd_bh:.2f}%")
    print(f"Sharpe Ratio: {sharpe_bh:.2f}")

    # Summary table
    print(f"\n{'=' * 80}")
    print(f"SUMMARY TABLE")
    print(f"{'=' * 80}")
    print(
        f"{'Strategy':<20} | {'Return':>8} | {'Win %':>7} | {'Trades':>7} | {'Max DD':>7} | {'Sharpe':>7}"
    )
    print(f"{'-' * 80}")
    print(
        f"{'Buy-and-Hold':<20} | {total_return_bh:>7.2f}% | {'N/A':>7} | {'1':>7} | {max_dd_bh:>6.2f}% | {sharpe_bh:>6.2f}"
    )
    print(
        f"{'Version A (Pure)':<20} | {total_return_a:>7.2f}% | {metrics_a['win_rate']:>6.1f}% | {metrics_a['total_trades']:>7} | {'N/A':>7} | {metrics_a['sharpe_ratio']:>6.2f}"
    )
    print(
        f"{'Version B (Opt)':<20} | {total_return_b:>7.2f}% | {metrics_b['win_rate']:>6.1f}% | {metrics_b['total_trades']:>7} | {'N/A':>7} | {metrics_b['sharpe_ratio']:>6.2f}"
    )
    print(
        f"{'Version C (TV)':<20} | {total_return_c:>7.2f}% | {metrics_c['win_rate']:>6.1f}% | {metrics_c['total_trades']:>7} | {'N/A':>7} | {metrics_c['sharpe_ratio']:>6.2f}"
    )
    print(f"{'=' * 80}")

    # Insights
    print(f"\nINSIGHTS:")
    print(f"{'=' * 80}")

    # Best performer
    returns = {
        "Buy-and-Hold": total_return_bh,
        "Version A": total_return_a,
        "Version B": total_return_b,
        "Version C": total_return_c,
    }
    best_strategy = max(returns, key=returns.get)
    print(f"Best Strategy: {best_strategy} ({returns[best_strategy]:+.2f}%)")

    # Trade frequency analysis
    print(f"\nTrade Frequency:")
    print(
        f"  Version A: {metrics_a['total_trades']} trades (~{metrics_a['total_trades'] / 730:.1f} trades/day)"
    )
    print(
        f"  Version B: {metrics_b['total_trades']} trades (~{metrics_b['total_trades'] / 730:.1f} trades/day)"
    )
    print(
        f"  Version C: {metrics_c['total_trades']} trades (~{metrics_c['total_trades'] / 730:.1f} trades/day)"
    )

    # Win rate comparison
    print(f"\nWin Rate Analysis:")
    print(f"  Version A: {metrics_a['win_rate']:.1f}% (Expected ~50.8% from analytics)")
    print(f"  Version B: {metrics_b['win_rate']:.1f}%")
    print(f"  Version C: {metrics_c['win_rate']:.1f}%")

    # Risk-adjusted returns
    print(f"\nRisk-Adjusted Performance:")
    print(f"  Version A Sharpe: {metrics_a['sharpe_ratio']:.2f}")
    print(f"  Version B Sharpe: {metrics_b['sharpe_ratio']:.2f}")
    print(f"  Version C Sharpe: {metrics_c['sharpe_ratio']:.2f}")

    # Time-based edge validation
    if total_return_a > total_return_bh * 0.5:
        print(
            f"\nTime-based edge appears to exist (Version A beats 50% of buy-and-hold)"
        )
    else:
        print(f"\nTime-based edge is weak or non-existent after transaction costs")

    # Filter effectiveness
    if metrics_c["total_trades"] < metrics_a["total_trades"] * 0.5:
        print(
            f"\nVersion C filters are too restrictive (only {metrics_c['total_trades']} vs {metrics_a['total_trades']} trades)"
        )
    else:
        print(f"\nVersion C filters maintain reasonable trade frequency")

    # Profitability assessment
    profitable_strategies = [k for k, v in returns.items() if v > 0]
    if profitable_strategies:
        print(f"\nProfitable Strategies: {', '.join(profitable_strategies)}")
    else:
        print(
            f"\nAll strategies were unprofitable - edge may not exist or transaction costs are too high"
        )

    print(f"{'=' * 80}\n")

    return {
        "timeframe": timeframe,
        "buy_and_hold": {
            "return": total_return_bh,
            "final_value": end_value_bh,
            "sharpe": sharpe_bh,
            "max_dd": max_dd_bh,
        },
        "version_a": {
            "return": total_return_a,
            "final_value": end_value_a,
            "win_rate": metrics_a["win_rate"],
            "trades": metrics_a["total_trades"],
            "sharpe": metrics_a["sharpe_ratio"],
            "profit_factor": metrics_a["profit_factor"],
            "avg_duration": metrics_a["avg_duration"],
        },
        "version_b": {
            "return": total_return_b,
            "final_value": end_value_b,
            "win_rate": metrics_b["win_rate"],
            "trades": metrics_b["total_trades"],
            "sharpe": metrics_b["sharpe_ratio"],
            "profit_factor": metrics_b["profit_factor"],
            "avg_duration": metrics_b["avg_duration"],
        },
        "version_c": {
            "return": total_return_c,
            "final_value": end_value_c,
            "win_rate": metrics_c["win_rate"],
            "trades": metrics_c["total_trades"],
            "sharpe": metrics_c["sharpe_ratio"],
            "profit_factor": metrics_c["profit_factor"],
            "avg_duration": metrics_c["avg_duration"],
        },
    }


def main():
    """Run backtests for both 1h and 4h timeframes"""
    print(f"\n{'=' * 80}")
    print(f"TIME-BASED STRATEGY BACKTEST SUITE")
    print(f"{'=' * 80}")
    print(f"Testing three versions of time-based edge strategy")
    print(f"With buy-and-hold baseline")
    print(f"Commission: 0.02% per trade")
    print(f"Initial Capital: $10,000")

    # Run 1h backtest
    results_1h = run_backtest(timeframe="1h")

    # Run 4h backtest
    results_4h = run_backtest(timeframe="4h")

    # Cross-timeframe comparison
    print(f"\n{'=' * 80}")
    print(f"CROSS-TIMEFRAME COMPARISON")
    print(f"{'=' * 80}")
    print(f"{'Strategy':<20} | {'1H Return':>11} | {'4H Return':>11} | {'Best':>6}")
    print(f"{'-' * 80}")
    print(
        f"{'Buy-and-Hold':<20} | {results_1h['buy_and_hold']['return']:>+10.2f}% | {results_4h['buy_and_hold']['return']:>+10.2f}% | {'1H' if results_1h['buy_and_hold']['return'] > results_4h['buy_and_hold']['return'] else '4H'}"
    )
    print(
        f"{'Version A (Pure)':<20} | {results_1h['version_a']['return']:>+10.2f}% | {results_4h['version_a']['return']:>+10.2f}% | {'1H' if results_1h['version_a']['return'] > results_4h['version_a']['return'] else '4H'}"
    )
    print(
        f"{'Version B (Opt)':<20} | {results_1h['version_b']['return']:>+10.2f}% | {results_4h['version_b']['return']:>+10.2f}% | {'1H' if results_1h['version_b']['return'] > results_4h['version_b']['return'] else '4H'}"
    )
    print(
        f"{'Version C (TV)':<20} | {results_1h['version_c']['return']:>+10.2f}% | {results_4h['version_c']['return']:>+10.2f}% | {'1H' if results_1h['version_c']['return'] > results_4h['version_c']['return'] else '4H'}"
    )
    print(f"{'=' * 80}")

    # Final recommendations
    print(f"\nFINAL RECOMMENDATIONS:")
    print(f"{'=' * 80}")

    # Find overall best strategy
    all_returns = {
        "1H Buy-and-Hold": results_1h["buy_and_hold"]["return"],
        "1H Version A": results_1h["version_a"]["return"],
        "1H Version B": results_1h["version_b"]["return"],
        "1H Version C": results_1h["version_c"]["return"],
        "4H Buy-and-Hold": results_4h["buy_and_hold"]["return"],
        "4H Version A": results_4h["version_a"]["return"],
        "4H Version B": results_4h["version_b"]["return"],
        "4H Version C": results_4h["version_c"]["return"],
    }

    best_overall = max(all_returns, key=all_returns.get)
    print(f"Overall Best Strategy: {best_overall} ({all_returns[best_overall]:+.2f}%)")

    # Edge assessment
    profitable_strategies = [k for k, v in all_returns.items() if v > 0]
    if len(profitable_strategies) > 0:
        print(f"\nProfitable Strategies ({len(profitable_strategies)}/8):")
        for strategy in sorted(
            profitable_strategies, key=all_returns.get, reverse=True
        ):
            print(f"  {strategy}: {all_returns[strategy]:+.2f}%")
    else:
        print(
            f"\nNo strategies were profitable - time-based edge may not exist at these transaction costs"
        )

    # Best version comparison
    version_returns = {
        "Version A": max(
            results_1h["version_a"]["return"], results_4h["version_a"]["return"]
        ),
        "Version B": max(
            results_1h["version_b"]["return"], results_4h["version_b"]["return"]
        ),
        "Version C": max(
            results_1h["version_c"]["return"], results_4h["version_c"]["return"]
        ),
    }
    best_version = max(version_returns, key=version_returns.get)
    print(f"\nBest Version: {best_version} ({version_returns[best_version]:+.2f}%)")

    # Timeframe recommendation
    timeframe_avg_1h = (
        results_1h["version_a"]["return"]
        + results_1h["version_b"]["return"]
        + results_1h["version_c"]["return"]
    ) / 3
    timeframe_avg_4h = (
        results_4h["version_a"]["return"]
        + results_4h["version_b"]["return"]
        + results_4h["version_c"]["return"]
    ) / 3

    if timeframe_avg_1h > timeframe_avg_4h:
        print(
            f"\nRecommended Timeframe: 1H (Avg: {timeframe_avg_1h:+.2f}% vs 4H: {timeframe_avg_4h:+.2f}%)"
        )
    else:
        print(
            f"\nRecommended Timeframe: 4H (Avg: {timeframe_avg_4h:+.2f}% vs 1H: {timeframe_avg_1h:+.2f}%)"
        )

    print(f"\n{'=' * 80}\n")


if __name__ == "__main__":
    main()
