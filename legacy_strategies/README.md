# Legacy Strategies

This folder contains **old strategy implementations** that were used before the new modular framework was created.

## ⚠️ DEPRECATED - Use New Framework Instead

These files are kept for **reference only** and should NOT be used for new work. Please use the new framework located in `src/`.

## Files

### 4H Strategy
- **`optimized_trend.py`** - Final optimized 4H trend strategy
  - Parameters: EMA(55, 144), SL 0.6x, TP 2.0x
  - Expected Return: +36.73%
  - Sharpe: 1.44

### 1H Strategies
- **`optimized_trend_1h_v2.py`** - Final optimized 1H trend strategy
  - Parameters: EMA(45, 80), SL 0.5x, TP 1.97x
  - Expected Return: +31.12%
  - Sharpe: 1.36

- **`enhanced_trend_1h.py`** - ADX-enhanced trend strategy
  - Adds ADX trend strength filter
  - Adds volatility-based position sizing

- **`optimized_trend_1h.py`** - Earlier 1H optimization attempt

### Other
- **`breakout_trend_1h.py`** - Breakout-based trend strategy

- **`trend_backtest_simple.py`** - Simple backtest implementation

## Migration to New Framework

To migrate these strategies to the new framework:

```python
from src.strategies.trend_following import TrendFollowingStrategy
from src.backtest.engine import BacktestEngine
from src.data.fetcher import DataFetcher

# Create config (same parameters as old strategy)
config = {
    "ema_fast": 55,
    "ema_slow": 144,
    "atr_period": 14,
    "atr_multiplier_sl": 0.6,
    "atr_multiplier_tp": 2.0,
    "rsi_period": 14,
    "position_size_pct": 0.7,
    "initial_capital": 10000
}

# Run strategy
strategy = TrendFollowingStrategy(config)
engine = BacktestEngine({"initial_capital": 10000})
results = engine.run(df, strategy)
```

## Benefits of New Framework

1. **Modular architecture** - Easy to extend
2. **Reusable components** - Indicators, fetcher, engine
3. **Multi-exchange support** - 6 exchanges supported
4. **Multi-timeframe support** - Any timeframe
5. **Built-in optimization** - Bayesian, grid, random search
6. **Better testing** - Train/test split, walk-forward analysis
7. **Cleaner code** - ~50 lines vs 200+ lines

See `FRAMEWORK_README.md` for complete documentation.
