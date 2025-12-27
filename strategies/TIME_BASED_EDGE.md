# Time-Based Edge Strategy

## Overview

This strategy implements the "Time-Based Edge" trading approach derived from the BTCUSDT analytics report. It leverages the statistical edge identified during specific UTC hours where the market shows positive bias.

## Strategy Logic

Based on 2 years of BTCUSDT 1H data:
- **17:00 UTC:** +0.052% average return
- **21:00 UTC:** +0.044% average return
- **22:00 UTC:** +0.049% average return

These hours show a consistent positive bias above random expectation.

## Entry Conditions

1. **Time filter:** Only trades during specified UTC hours (17:00, 21:00, 22:00 by default)
2. **Momentum confirmation:** Previous hour closed green
3. **Volume confirmation:** Previous hour volume > 20-period average
4. **Trend confirmation:** Current hour close > 5-period SMA

## Exit Conditions

1. **Profit target:** 0.8% (configurable)
2. **Stop loss:** 0.5% (configurable)
3. **Time-based exit:** Close position at end of trading hour if not profitable

## Risk Management

- Default position size: 5% of equity
- Commission: 0.1% per trade
- Both long and short modes available
- Hour-based exit prevents holding losing positions

## Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| Trading Hour 1 (UTC) | 17 | 0-23 | First high-probability trading hour |
| Trading Hour 2 (UTC) | 21 | 0-23 | Second high-probability trading hour |
| Trading Hour 3 (UTC) | 22 | 0-23 | Third high-probability trading hour |
| Profit Target % | 0.8 | 0.1-5.0 | Target profit per trade |
| Stop Loss % | 0.5 | 0.1-3.0 | Maximum loss per trade |
| Long Trades Only | true | - | Enable only long positions |
| Short Trades Only | false | - | Enable only short positions |

## How to Use

1. Open TradingView
2. Go to Pine Editor
3. Copy the strategy code
4. Apply to BTCUSDT 1H chart
5. Adjust parameters as needed

## Expected Performance

Based on historical analytics:
- **Win rate:** ~52-55% (vs 50% random)
- **Edge:** 2-5% above random
- **Trade frequency:** ~3 trades per day (during specified hours)
- **Risk:** Limited to stop loss and hour-end exit

## Customization Tips

1. **For different timezones:** Adjust trading hours accordingly
   - US Eastern: Add 5 hours to UTC
   - US Pacific: Add 8 hours to UTC
   - European Central: Add 1 hour to UTC

2. **For more aggressive trading:**
   - Increase profit target to 1.2-1.5%
   - Reduce stop loss to 0.3-0.4%
   - Add more trading hours with slight edge

3. **For more conservative trading:**
   - Reduce profit target to 0.5-0.6%
   - Increase stop loss to 0.7-1.0%
   - Only trade 1-2 best hours

## Limitations

- Historical edge doesn't guarantee future performance
- Works best during normal market conditions
- May underperform during extreme volatility events
- Requires proper risk management

## Backtesting

Always backtest on historical data before live trading:
1. Set date range covering at least 6 months
2. Compare buy-and-hold performance
3. Analyze maximum drawdown
4. Check win rate consistency across periods

## Important Notes

- This is a low-edge strategy (2-5% above random)
- Use small position sizes (5% or less per trade)
- Consider combining with other strategies
- Monitor performance quarterly
- Adjust parameters if edge disappears

## Code Version

- PineScript Version 6
- Compatible with all TradingView platforms
- No external dependencies
