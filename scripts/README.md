# Scripts

This folder contains **old utility scripts** that were used before the new framework was created.

## ⚠️ DEPRECATED - Use New Framework Instead

These scripts are kept for **reference only**. For new work, use the framework components in `src/`.

## Files

### Data Fetching Scripts
- **`btc_data_fetcher.py`** - Old BTC 4H data fetcher
- **`btc_data_fetcher_1h.py`** - Old BTC 1H data fetcher

**Replacement**: Use `src/data/fetcher.py` which supports multiple exchanges and timeframes.

### Optimization Scripts
- **`random_search_1h.py`** - Random search for 1H parameters
- **`enhanced_grid_search_1h.py`** - Grid search with overfitting prevention
- **`robust_grid_search.py`** - Robust grid search for 4H
- **`robust_grid_search_1h.py`** - Robust grid search for 1H

**Replacement**: Use `src/optimization/bayesian_opt.py` (more efficient).

### Analysis Scripts
- **`overfitting_analysis.py`** - Analysis of parameter overfitting

**Replacement**: Use framework's built-in train/test split and walk-forward analysis.

## Migration Examples

### Old Way (Deprecated)
```python
from btc_data_fetcher import fetch_btc_data_4h
from robust_grid_search import run_robust_grid_search

df = fetch_btc_data_4h()
best_params = run_robust_grid_search(df)
```

### New Way (Framework)
```python
from src.data.fetcher import DataFetcher
from src.optimization.bayesian_opt import BayesianOptimizer
from src.strategies import TrendFollowingStrategy

# Fetch data (multi-exchange, multi-timeframe)
fetcher = DataFetcher(exchange="binance")
df = fetcher.fetch("BTC/USDT", "4h", period_days=730)

# Optimize (10-50x faster than grid search)
optimizer = BayesianOptimizer(
    strategy_class=TrendFollowingStrategy,
    df=df,
    engine_config={"initial_capital": 10000},
    n_trials=100
)
results = optimizer.optimize()
```

## Benefits of New Framework

| Feature | Old Scripts | New Framework |
|---------|-------------|---------------|
| Exchanges | Binance only | 6 exchanges |
| Timeframes | Fixed | Any timeframe |
| Optimization | Grid/Random | Bayesian (10-50x faster) |
| Code Reuse | Duplicated | Reusable components |
| Testing | Basic | Train/test, walk-forward |
| Extensibility | Hard | Easy (~20 lines) |

See `FRAMEWORK_README.md` for complete documentation.
