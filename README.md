# Optimized Trend Following Strategy - BTC/USDT 4H

A trend-following trading strategy optimized for Bitcoin on the 4-hour timeframe using EMA crossovers, ATR-based risk management, and RSI filters.

## Strategy Overview

This strategy uses mean reversion to trend following by entering positions when price pulls back to the fast EMA (55) while the overall trend remains bullish (price > slow EMA 144). Risk is managed using dynamic ATR-based stops.

## Key Parameters

- **EMA Fast**: 55 (pullback detection)
- **EMA Slow**: 144 (trend direction)
- **ATR Period**: 14 (volatility measurement)
- **Stop Loss**: 0.6 × ATR
- **Take Profit**: 2.5 × ATR
- **RSI Period**: 14 (momentum filter)
- **Position Size**: 70% of equity

## Entry Conditions

**Long Entry:**
- Price > EMA 144 (bullish trend)
- Price within 1% of EMA 55 (pullback)
- RSI < 70 (not overbought)
- Volume ≥ 20-period average

**Short Entry:**
- Price < EMA 144 (bearish trend)
- Price within 1% of EMA 55 (pullback)
- RSI > 30 (not oversold)
- Volume ≥ 20-period average

## Exit Conditions

1. **Stop Loss Hit**: Price moves 0.6 × ATR against position
2. **Take Profit Hit**: Price moves 2.5 × ATR in favor of position
3. **Trend Reversal**: Price crosses EMA 144

## Performance Results (2 Years, 4H Timeframe)

### Strategy
- **Total Return**: +41.35%
- **Final Capital**: $14,135
- **Win Rate**: 30.4%
- **Sharpe Ratio**: 1.49
- **Max Drawdown**: -14.82%
- **Total Trades**: 158

### Buy & Hold Baseline
- **Total Return**: +108.36%
- **Sharpe Ratio**: 0.34
- **Max Drawdown**: -34.37%

### Comparison

The strategy provides **significantly better risk-adjusted returns**:
- Sharpe ratio 4.4x higher (1.49 vs 0.34)
- 57% lower drawdown (-14.82% vs -34.37%)
- Outperforms Buy & Hold during market corrections

However, it **underperforms in strong bull markets** (expected behavior) because:
- Frequent exits during corrections miss subsequent rallies
- Transaction costs accumulate
- Timing lag causes re-entries at higher prices

## Files

- **optimized_trend.py** - Python backtest implementation with equity curves and monthly returns
- **trend_backtest_simple.py** - Grid search optimization to find best parameters (4,374+ combinations tested)
- **optimized_trend_strategy.pine** - TradingView PineScript v6 version
- **btc_data_fetcher.py** - Data fetching utility from Binance

## Usage

### Grid Search Optimization

```bash
python trend_backtest_simple.py
```

This will:
1. Fetch 2 years of BTC/USDT 4H data from Binance
2. Test 4,374+ parameter combinations
3. Find optimal parameters that maximize risk-adjusted returns
4. Display best configuration and performance metrics

### Python Backtest (Using Optimized Parameters)

```bash
python optimized_trend.py
```

This will:
1. Fetch 2 years of BTC/USDT 4H data from Binance
2. Run the strategy backtest
3. Display performance metrics
4. Generate two visualizations:
   - `optimized_trend_equity_curve.png` - Strategy vs Buy & Hold equity curves
   - `optimized_trend_monthly_returns.png` - Monthly returns comparison

### TradingView

1. Open `optimized_trend_strategy.pine` in TradingView
2. Apply to BTC/USDT 4H chart
3. Adjust parameters in the settings panel
4. View backtest results in the Strategy Tester tab

## Dependencies

```bash
pip install pandas numpy matplotlib ccxt
```

## Best Use Cases

✓ **Risk-averse investors** wanting lower drawdowns
✓ **Sideways/ranging markets** where Buy & Hold suffers
✓ **Bear markets** where shorting provides protection
✓ When prioritizing **Sharpe ratio** over total return

## Worst Use Cases

✗ **Strong multi-year bull runs** (like tested period)
✗ **Parabolic rallies** with few corrections
✗ Assets with **guaranteed long-term uptrend**

## Expected Performance

- **Strong Bull**: Underperforms Buy & Hold significantly
- **Sideways**: Outperforms Buy & Hold
- **Bear**: Outperforms Buy & Hold (by shorting)

## Recommendations

1. Use as a **risk management tool**, not return maximizer
2. Consider **hybrid approach**: 50% Buy & Hold + 50% Active
3. Combine with **regime detection** to switch strategies
4. Backtest on **your specific market/timeframe** before use

## Notes

This strategy was optimized for BTC/USDT on 4H timeframe (Dec 2023 - Dec 2025). Past performance does not guarantee future results. Always use proper position sizing and risk management.
