# Results

This folder contains **backtest results and visualization outputs** from previous strategy runs.

## Files

### Equity Curves
- **`optimized_trend_equity_curve.png`** - 4H optimized strategy equity
- **`optimized_trend_1h_equity_curve.png`** - 1H optimized strategy equity (v1)
- **`optimized_trend_1h_v2_equity_curve.png`** - 1H optimized strategy equity (v2)
- **`enhanced_trend_1h_equity_curve.png`** - ADX-enhanced 1H strategy equity
- **`breakout_1h_equity_curve.png`** - 1H breakout strategy equity

### Other Results
- **`optimized_trend_monthly_returns.png`** - Monthly returns breakdown

## Performance Summary

| Strategy | Timeframe | Return | Sharpe | Trades | Win Rate |
|----------|-----------|--------|--------|---------|-----------|
| Optimized Trend | 4H | +36.73% | 1.44 | 170 | 34.1% |
| Optimized Trend 1H v2 | 1H | +31.12% | 1.36 | 726 | 35.4% |
| Enhanced Trend 1H | 1H | +24.67% | 1.21 | 563 | 33.4% |

## Note

These results are from **legacy strategy implementations**. For new strategies, use the framework:

```python
from src.data.fetcher import DataFetcher
from src.strategies.trend_following import TrendFollowingStrategy
from src.backtest.engine import BacktestEngine

fetcher = DataFetcher(exchange="binance")
df = fetcher.fetch("BTC/USDT", "4h", period_days=730)

strategy = TrendFollowingStrategy(config)
engine = BacktestEngine({"initial_capital": 10000})
results = engine.run(df, strategy)
```

See `FRAMEWORK_README.md` for complete documentation.
