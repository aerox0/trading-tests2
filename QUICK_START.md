# Quick Start Guide - Trading Framework

## Installation

```bash
# Add dependencies
uv add pandas numpy ccxt matplotlib seaborn optuna pyyaml
```

## 5-Minute Example: Backtest

```python
from src.data.fetcher import DataFetcher
from src.strategies.trend_following import TrendFollowingStrategy
from src.backtest.engine import BacktestEngine

# 1. Fetch data
fetcher = DataFetcher(exchange='binance')
df = fetcher.fetch('BTC/USDT', '4h', 365)

# 2. Setup strategy
config = {
    'ema_fast': 55,
    'ema_slow': 144,
    'atr_period': 14,
    'atr_multiplier_sl': 0.6,
    'atr_multiplier_tp': 2.0,
    'rsi_period': 14,
    'volume_multiplier': 1.0,
    'position_size_pct': 0.7,
    'initial_capital': 10000
}

strategy = TrendFollowingStrategy(config)

# 3. Run backtest
engine = BacktestEngine({'initial_capital': 10000})
results = engine.run(df, strategy)

print(f"Return: {results['total_return']:+.2f}%")
print(f"Sharpe: {results['sharpe_ratio']:.2f}")
print(f"Trades: {results['total_trades']}")
```

## 5-Minute Example: Optimization

```python
from src.data.fetcher import DataFetcher
from src.strategies.trend_following import TrendFollowingStrategy
from src.optimization.bayesian_opt import BayesianOptimizer
from src.backtest.engine import BacktestEngine

# 1. Fetch data
fetcher = DataFetcher()
df = fetcher.fetch('BTC/USDT', '4h', 365)

# 2. Bayesian optimization (BEST method)
optimizer = BayesianOptimizer(
    strategy_class=TrendFollowingStrategy,
    df=df,
    engine_config={'initial_capital': 10000},
    n_trials=100  # Start with 100, can go higher
)

results = optimizer.optimize()

print(f"Best Parameters: {results['best_params']}")
print(f"Best Sharpe: {results['best_objective']:.2f}")
print(f"Backtest Return: {results['backtest_results']['total_return']:+.2f}%")
```

## 10-Minute Example: Multi-Asset Backtest

```python
from src.data.fetcher import DataFetcher
from src.strategies.trend_following import TrendFollowingStrategy
from src.backtest.engine import BacktestEngine

# 1. Setup
config = {
    'ema_fast': 55,
    'ema_slow': 144,
    'atr_period': 14,
    'atr_multiplier_sl': 0.6,
    'atr_multiplier_tp': 2.0,
    'rsi_period': 14,
    'volume_multiplier': 1.0,
    'position_size_pct': 0.7,
    'initial_capital': 10000
}

fetcher = DataFetcher()
engine = BacktestEngine({'initial_capital': 10000})

# 2. Test multiple assets
assets = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
timeframes = ['1h', '4h']

for symbol in assets:
    for timeframe in timeframes:
        df = fetcher.fetch(symbol, timeframe, 365)
        strategy = TrendFollowingStrategy(config)
        results = engine.run(df, strategy)
        
        print(f"{symbol} {timeframe}: {results['total_return']:+.2f}% | "
              f"Sharpe {results['sharpe_ratio']:.2f}")
```

## Creating Custom Strategy

```python
from src.core.base_strategy import BaseStrategy
from src.indicators import EMA, ATR, RSI
import pandas as pd

class MyCustomStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.ema = EMA()
        self.atr = ATR()
        self.rsi = RSI()

    def calculate_indicators(self, df):
        df['ema'] = self.ema.calculate(df, self.config['ema_period'])
        df['atr'] = self.atr.calculate(df, 14)
        df['rsi'] = self.rsi.calculate(df, 14)
        return df

    def generate_signals(self, df):
        df['buy'] = (df['close'] > df['ema']) & (df['rsi'] < 30)
        df['sell'] = (df['close'] < df['ema']) & (df['rsi'] > 70)
        return df

    def execute_trade(self, df, index):
        # Your trade logic
        pass
```

## Optimization Methods Comparison

| Method | Speed | Efficiency | Best For |
|--------|-------|------------|----------|
| **Bayesian** | ★★★★★ | ★★★★★ | High-dimensional spaces (10+ params) |
| Random | ★★★★ | ★★★★ | Quick exploration, medium spaces |
| Grid | ★★ | ★★ | Small spaces, exhaustive search |

**Recommendation**: Always start with Bayesian optimization (fastest and most efficient).

## File Structure Quick Reference

```
src/
├── core/              # Base classes (don't modify)
├── data/              # Data fetching (DataFetcher class)
├── indicators/         # Indicators (EMA, ATR, RSI, ADX, Donchian)
├── strategies/         # Your strategies go here
├── backtest/          # Backtest engine (BacktestEngine)
├── optimization/       # Optimizers (Bayesian recommended)
└── analysis/          # Analysis tools (overfitting, walk-forward)
```

## Common Tasks

### Test Different Timeframes
```python
for tf in ['1h', '4h', '1d']:
    df = fetcher.fetch('BTC/USDT', tf, 365)
    results = engine.run(df, strategy)
    print(f"{tf}: {results['total_return']:+.2f}%")
```

### Test Different Exchanges
```python
for exchange in ['binance', 'bybit', 'okx']:
    fetcher = DataFetcher(exchange)
    df = fetcher.fetch('BTC/USDT', '4h', 365)
    results = engine.run(df, strategy)
    print(f"{exchange}: {results['total_return']:+.2f}%")
```

### Run with Train/Test Split
```python
from src.data.splitter import TrainTestSplitter

train_df, test_df = TrainTestSplitter.split_sequential(df, train_pct=0.7)

# Optimize on train
optimizer = BayesianOptimizer(strategy_class, train_df, engine_config, n_trials=50)
best_params = optimizer.optimize()

# Test on out-of-sample
strategy = TrendFollowingStrategy(best_params['best_params'])
test_results = engine.run(test_df, strategy)

print(f"Train Return: {results['backtest_results']['total_return']:+.2f}%")
print(f"Test Return: {test_results['total_return']:+.2f}%")
```

## Key Benefits

1. **Easy Strategy Creation**: 20 lines to add new strategy
2. **Multi-Asset**: Test BTC, ETH, SOL in one loop
3. **Multi-Timeframe**: Test 1H, 4H, 1D easily  
4. **Optimization**: Bayesian finds best params fast
5. **Production-Ready**: Clean architecture, type hints
6. **Extensible**: Add indicators/strategies without touching core

## Migration from Old Code

**Old approach** (monolithic files):
- 200+ lines per strategy
- Duplicate indicator code
- Hard to test multiple assets
- No optimization tools

**New framework**:
- 50 lines per strategy (75% reduction)
- Reusable indicators
- Multi-asset support built-in
- Bayesian/Grid/Random optimization
- Overfitting detection
- Walk-forward analysis
