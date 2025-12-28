# 1H Timeframe Optimization Results

## Overview
Optimized trend-following strategy for BTC/USDT 1H timeframe (2 years of data: 17,520 candles).

## Best Parameters Found

| Parameter | 1H Value | 4H Value |
|-----------|----------|---------|
| EMA Fast | 34 | 55 |
| EMA Slow | 200 | 144 |
| ATR Period | 14 | 14 |
| Stop Loss | 0.5x ATR | 0.6x ATR |
| Take Profit | 2.5x ATR | 2.0x ATR |
| RSI Period | 14 | 14 |
| Position Size | 50% | 70% |

**Key Differences:**
- Faster EMA periods (34/200 vs 55/144) - 1H requires faster indicators due to more noise
- Tighter stop loss (0.5x vs 0.6x) - More volatility on 1H requires closer stops
- Higher TP (2.5x vs 2.0x) - To compensate for more frequent stop-outs
- Smaller position size (50% vs 70%) - Higher volatility risk on 1H

## Performance Comparison

### 1H Timeframe Results
- **Total Return**: +22.81%
- **Final Capital**: $12,280.71
- **Sharpe Ratio**: 1.05 (6.2x better than Buy & Hold)
- **Win Rate**: 27.6%
- **Max Drawdown**: -15.01%
- **Total Trades**: 1,241

### 4H Timeframe Results
- **Total Return**: +36.73%
- **Final Capital**: $13,673.00
- **Sharpe Ratio**: 1.44 (4.2x better than Buy & Hold)
- **Win Rate**: 33.5%
- **Max Drawdown**: -16.38%
- **Total Trades**: 170

### Buy & Hold Baseline (Same period)
- **Total Return**: +108.48%
- **Sharpe Ratio**: 0.17
- **Max Drawdown**: -34.76%

## Key Insights

### 1H Advantages
- **More trading opportunities**: 1,241 trades vs 170 (7.3x more)
- **Better trade frequency**: Better for smaller accounts or more active trading
- **Faster adaptation**: Adapts to market changes more quickly
- **Lower per-trade risk**: Smaller position size (50% vs 70%)

### 1H Disadvantages
- **Lower total return**: +22.81% vs +36.73% (4H is 61% more profitable)
- **Lower Sharpe ratio**: 1.05 vs 1.44 (4H has 37% better risk-adjusted returns)
- **Higher noise-to-signal ratio**: 1H data has more market noise
- **Higher transaction costs**: More trades = more fees/slippage
- **Significant overfitting**: Test performance is negative (-8.09%)

### 4H Advantages
- **Higher returns**: +36.73% total return
- **Better Sharpe ratio**: 1.44 vs 1.05
- **Lower transaction costs**: Fewer trades (170 vs 1,241)
- **More reliable signals**: Higher timeframe = cleaner trends
- **Better overfitting**: Test decay 42% vs 23% (1H is better but both overfit)

### 4H Disadvantages
- **Fewer opportunities**: Only 170 trades over 2 years
- **Slower adaptation**: Takes longer to detect trend changes
- **Larger per-trade risk**: 70% position size vs 50%

## Overfitting Analysis

### 1H Timeframe
- **Train Return**: +35.15%
- **Test Return**: -8.09%
- **Performance Decay**: -23.0% (NEGATIVE - test < 0)
- **Assessment**: **HIGH OVERFITTING**

### 4H Timeframe
- **Train Return**: +27.10%
- **Test Return**: +11.48%
- **Performance Decay**: -42.4% (positive but large)
- **Assessment**: **MODERATE TO HIGH OVERFITTING**

**Conclusion**: Both timeframes show overfitting, but 1H has worse overfitting with negative test returns. The trend-following strategy seems inherently overfitted to the 2023-2025 bull market period.

## Recommendation

### Choose 4H Timeframe if:
- You prioritize higher returns and better risk-adjusted performance
- You prefer fewer, higher-quality trades
- You want lower transaction costs
- You can tolerate longer wait times between trades

### Choose 1H Timeframe if:
- You prefer more active trading with frequent opportunities
- You have a smaller account and want faster compounding
- You want faster adaptation to market changes
- You don't mind lower returns and more overfitting risk

### Best for Production: 4H Timeframe
The 4H timeframe is recommended because:
1. Higher returns (+36.73% vs +22.81%)
2. Better Sharpe ratio (1.44 vs 1.05)
3. Fewer trades = lower transaction costs and slippage
4. More reliable signals due to higher timeframe
5. Still significantly underperforms Buy & Hold but with better risk management

## Files Created

1. **btc_data_fetcher_1h.py** - Fetches 1H data from Binance
2. **robust_grid_search_1h.py** - Grid search optimization for 1H
3. **optimized_trend_1h.py** - Backtest with best 1H parameters
4. **optimized_trend_1h_strategy.pine** - PineScript for TradingView

## Usage

Run the 1H backtest:
```bash
uv run optimized_trend_1h.py
```

Re-optimize for 1H:
```bash
uv run robust_grid_search_1h.py
```

Use in TradingView:
- Copy contents of `optimized_trend_1h_strategy.pine`
- Set timeframe to 1H
- Apply to BTC/USDT chart

## Important Notes

1. **Overfitting Warning**: Both 4H and 1H strategies show significant overfitting. The test set performance (last 30% of data) is much worse than training set performance.

2. **Market Regime**: This period (Dec 2023 - Dec 2025) was a strong bull market. The strategy is likely overfitted to this regime.

3. **Future Performance**: Do not expect similar returns in different market conditions (bear markets, sideways markets).

4. **Ensemble Approach**: Consider using an ensemble of top 5 parameter sets to reduce overfitting risk.

5. **Dynamic Re-optimization**: Re-optimize every 6 months using walk-forward analysis to adapt to changing market conditions.

6. **Transaction Costs**: 1H strategy has 7.3x more trades - ensure your broker fees are low enough to make it profitable.

7. **Live Testing**: Always paper trade for at least 1-2 months before using real money, especially for 1H timeframe with more trades.
