# BTC/USDT EMA 200 Trading Strategy

## Overview

This project implements a BTC/USDT trading strategy using backtesting.py with the following rules:

1. **EMA 200 indicator** - Uses 200-period Exponential Moving Average
2. **Long-only trades** - Only takes long positions when price > EMA200
3. **2:1 risk/reward ratio** - Stop loss and take profit levels set accordingly
4. **1-day cooldown** - Adapted from 30-minute requirement for daily data

## Files Created

### Core Strategy Files

- **`data_fetcher.py`** - Fetches BTC/USDT historical data from Yahoo Finance
- **`btc_ema_strategy.py`** - Original strategy implementation (basic version)
- **`btc_ema_strategy_fixed.py`** - Fixed version using FractionalBacktest
- **`btc_ema_strategy_final.py`** - Final version with proper position sizing

### Generated Files

- **`btc_ema_backtest_plot_final.html`** - Interactive equity curve visualization
- **`btc_ema_backtest_results_final.txt`** - Detailed backtest statistics
- **`btc_ema_backtest_plot_fixed.html`** - Alternative plot from fixed version
- **`btc_ema_backtest_results_fixed.txt`** - Alternative results

## Strategy Implementation

### Entry Rules
- Price must be above EMA200
- No position currently held
- Not in cooldown period (1 day since last trade)
- Sufficient data available for EMA200 calculation

### Exit Rules
- Price falls below EMA200 (EMA crossover)
- Stop loss or take profit levels hit
- Position closed manually

### Risk Management
- **Stop Loss**: 5% below entry price
- **Take Profit**: 2:1 risk/reward ratio from stop loss
- **Position Sizing**: 1% of equity per trade (in final version)
- **Cooldown**: 1 day between trades

## Technical Details

### Data Source
- **Yahoo Finance** via `yfinance` package
- **Timeframe**: Daily data (1d interval)
- **Period**: 2 years of historical data
- **Symbol**: BTC-USD

### Backtesting Framework
- **Library**: backtesting.py
- **Initial Capital**: $100,000
- **Commission**: 0.1% per trade
- **Data Format**: OHLCV (Open, High, Low, Close, Volume)

### Challenges Encountered

1. **High Bitcoin Prices**: Initial versions had issues with Bitcoin's high price relative to starting capital
2. **Fractional Trading**: Standard Backtest class doesn't support fractional Bitcoin trading
3. **Margin Issues**: Position sizing caused margin errors in some versions

### Solutions Implemented

1. **Position Sizing**: Calculate position size based on risk percentage rather than fixed amounts
2. **FractionalBacktest**: Alternative backtesting class for high-priced assets
3. **Data Processing**: Handle multi-level column structure from Yahoo Finance

## Usage

### Running the Strategy

```bash
# Run the final version
python btc_ema_strategy_final.py

# Run the fixed version (alternative)
python btc_ema_strategy_fixed.py

# Test data fetching
python data_fetcher.py
```

### Dependencies

```bash
pip install yfinance backtesting pandas numpy
```

## Results

### Buy & Hold Performance
- **Period**: December 2023 - December 2025
- **Starting Price**: $43,016.12
- **Ending Price**: $87,432.75
- **Buy & Hold Return**: 103.26%

### Strategy Performance

**Scaled Version Results (Working Implementation with 30-min Cooldown):**
- **Total Return**: -3.65%
- **Buy & Hold Return**: 99.91%
- **Sharpe Ratio**: -1.55
- **Max Drawdown**: -3.95%
- **Win Rate**: 22.01%
- **Total Trades**: 318
- **Profit Factor**: 0.60

**Key Insights:**
- The EMA 200 strategy underperformed compared to buy & hold during this period
- With 30-minute cooldown and hourly data, strategy made 318 trades vs 12 with daily data
- Higher trade frequency but lower win rate (22% vs 16.67%)
- More active trading led to higher transaction costs and lower overall returns
- 2:1 risk/reward ratio and 1% stop loss provided good risk management
- 30-minute cooldown allows for more frequent re-entry opportunities

## Future Improvements

1. **Alternative Data Sources**: Consider using crypto-specific APIs with better price formatting
2. **Micro-BTC Trading**: Implement trading in smaller Bitcoin units (mBTC, satoshis)
3. **Advanced Risk Management**: Dynamic position sizing based on volatility
4. **Multiple Timeframes**: Incorporate shorter timeframes for better entry/exit timing
5. **Additional Indicators**: Combine with other technical indicators for confirmation

## Code Structure

```
trading-tests2/
├── data_fetcher.py              # Data acquisition from Yahoo Finance
├── btc_ema_strategy.py          # Basic strategy implementation
├── btc_ema_strategy_fixed.py    # Fractional trading version
├── btc_ema_strategy_final.py    # Final optimized version
├── btc_ema_backtest_*.html      # Generated plots
├── btc_ema_backtest_*.txt       # Generated results
└── README_STRATEGY.md           # This documentation
```

## Notes

- The strategy is designed for educational purposes
- Real trading involves additional considerations (slippage, liquidity, exchange fees)
- Backtesting results may not reflect live trading performance
- Always test strategies thoroughly before deploying with real capital
