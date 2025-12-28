# Trading Framework - Modular & Extensible

A modular, extensible framework for crypto trading strategies with support for multiple assets, timeframes, exchanges, and optimization methods.

## Architecture Overview

```
src/
├── core/              # Base classes and abstractions
│   ├── base_strategy.py   # Abstract strategy interface
│   ├── base_indicator.py   # Abstract indicator interface
│   ├── base_backtest.py   # Abstract backtest engine
│   └── config.py          # Configuration management (YAML)
│
├── data/              # Data fetching and processing
│   ├── fetcher.py        # Universal multi-exchange fetcher
│   └── splitter.py       # Train/test split utilities
│
├── indicators/         # Technical indicators (reusable)
│   ├── ema.py           # Exponential Moving Average
│   ├── atr.py           # Average True Range
│   ├── rsi.py           # Relative Strength Index
│   ├── adx.py           # Average Directional Index
│   └── donchian.py      # Donchian Channels
│
├── strategies/         # Trading strategies
│   ├── trend_following.py  # EMA pullback strategy
│   ├── pullback.py        # Pullback to EMA
│   └── breakout.py        # Donchian breakout
│
├── backtest/          # Backtesting engine
│   └── engine.py         # Strategy execution
│
├── optimization/       # Parameter optimization
│   ├── bayesian_opt.py   # Bayesian (Optuna) - BEST
│   ├── grid_search.py     # Grid search
│   ├── random_search.py   # Random search
│   └── walk_forward.py    # Walk-forward analysis
│
├── analysis/           # Analysis tools
│   ├── metrics.py        # Performance metrics
│   ├── overfitting.py    # Overfitting detection
│   ├── monte_carlo.py    # Monte Carlo simulation
│   └── sensitivity.py     # Parameter sensitivity
│
└── visualization/      # Visualization and reporting
    ├── plots.py          # Plotting utilities
    └── reports.py        # Report generation
```

## Key Features

### 1. **Universal Data Fetcher**
- Multi-exchange support (Binance, Coinbase, Kraken, Bybit, OKX, KuCoin)
- Multi-timeframe support (1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M)
- Automatic batch fetching for large date ranges
- Built-in Buy & Hold baseline calculation

**Usage:**
```python
from src.data.fetcher import DataFetcher

fetcher = DataFetcher(exchange='binance')
df = fetcher.fetch(symbol='BTC/USDT', timeframe='4h', period_days=730)
```

### 2. **Modular Indicators**
All indicators inherit from `BaseIndicator` with consistent interface:

```python
from src.indicators import EMA, ATR, RSI

ema = EMA()
atr = ATR()
rsi = RSI()

df['ema'] = ema.calculate(df, period=20)
df['atr'] = atr.calculate(df, period=14)
df['rsi'] = rsi.calculate(df, period=14)
```

### 3. **Strategy Interface**
All strategies inherit from `BaseStrategy` and implement:

- `calculate_indicators()` - Add indicators to DataFrame
- `generate_signals()` - Create buy/sell signals
- `execute_trade()` - Trade execution logic

**Example - Creating Custom Strategy:**
```python
from src.core.base_strategy import BaseStrategy
from src.indicators import EMA, ATR

class MyStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.ema = EMA()
        self.atr = ATR()
    
    def calculate_indicators(self, df):
        df['ema'] = self.ema.calculate(df, self.config['ema_period'])
        df['atr'] = self.atr.calculate(df, 14)
        return df
    
    def generate_signals(self, df):
        df['buy'] = df['close'] > df['ema']
        df['sell'] = df['close'] < df['ema']
        return df
    
    def execute_trade(self, df, index):
        # Your trade logic here
        pass
```

### 4. **Configuration Management (YAML)**
Strategies configured via YAML files:

```yaml
# config/strategies/my_strategy.yaml
strategy:
  name: "My Strategy"
  class: "MyStrategy"

asset:
  symbol: "BTC/USDT"
  timeframe: "4h"
  exchange: "binance"

parameters:
  ema_period: 20
  atr_period: 14
  position_size_pct: 0.5

backtest:
  initial_capital: 10000
  period_days: 730
  commission: 0.001
```

**Usage:**
```python
from src.core.config import Config

config = Config('config/strategies/my_strategy.yaml')
params = config.get_strategy_params()
```

### 5. **Backtest Engine**
Run backtests with any strategy:

```python
from src.backtest.engine import BacktestEngine
from src.strategies import TrendFollowingStrategy

strategy = TrendFollowingStrategy(config)
engine = BacktestEngine(engine_config)
results = engine.run(df, strategy)
```

### 6. **Optimization Methods**

#### Bayesian Optimization (BEST - Recommended)
Uses Optuna's Gaussian Process for efficient high-dimensional optimization:

```python
from src.optimization import BayesianOptimizer

optimizer = BayesianOptimizer(
    strategy_class=TrendFollowingStrategy,
    df=df,
    engine_config=engine_config,
    n_trials=100  # Number of trials
)

results = optimizer.optimize()
print(f"Best params: {results['best_params']}")
print(f"Best Sharpe: {results['best_objective']:.2f}")
```

**Advantages:**
- Most efficient for high-dimensional spaces
- Learns from previous trials
- Finds global optimum faster
- ~10-50x fewer trials than grid search

#### Grid Search
Exhaustive search over parameter grid:

```python
from src.optimization import GridSearchOptimizer

optimizer = GridSearchOptimizer(
    strategy_class=TrendFollowingStrategy,
    df=df,
    param_grid={...}
)

results = optimizer.optimize()
```

#### Random Search
Random parameter sampling:

```python
from src.optimization import RandomSearchOptimizer

optimizer = RandomSearchOptimizer(
    strategy_class=TrendFollowingStrategy,
    df=df,
    n_iterations=500
)

results = optimizer.optimize()
```

**Advantages:**
- Simple and fast
- No parameter constraints
- Finds parameters not in grid
- 98% more efficient than full grid

### 7. **Analysis Tools**

#### Overfitting Detection
Detect if strategy is overfitted to training data:

```python
from src.analysis import OverfittingDetector

detector = OverfittingDetector()
results = detector.analyze(strategy, df, train_pct=0.7)

if results['decay'] < 0.5:
    print("✗ HIGH overfitting")
elif results['decay'] < 0.7:
    print("⚠ MODERATE overfitting")
else:
    print("✓ GOOD: Low overfitting")
```

#### Walk-Forward Analysis
Test robustness with rolling windows:

```python
from src.analysis import WalkForwardAnalyzer

analyzer = WalkForwardAnalyzer()
results = analyzer.analyze(strategy, df, train_size=500, test_size=100)

print(f"Mean return: {results['mean_return']:.2f}%")
print(f"Std deviation: {results['std_return']:.2f}%")
```

#### Monte Carlo Simulation
Test strategy stability with resampled data:

```python
from src.analysis import MonteCarlo

mc = MonteCarlo()
results = mc.run(strategy, df, n_simulations=1000)

print(f"5th percentile: {results['p5_return']:.2f}%")
print(f"95th percentile: {results['p95_return']:.2f}%")
```

## Multi-Asset & Multi-Timeframe Support

**Test Multiple Assets:**
```python
from src.data.fetcher import DataFetcher

fetcher = DataFetcher()
assets = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

data = fetcher.fetch_multiple(
    symbols=assets,
    timeframe='4h',
    period_days=730
)

for symbol, df in data.items():
    results = engine.run(df, strategy)
    print(f"{symbol}: {results['total_return']:+.2f}%")
```

**Test Multiple Timeframes:**
```python
timeframes = ['1h', '4h', '1d']

for tf in timeframes:
    df = fetcher.fetch(symbol='BTC/USDT', timeframe=tf)
    results = engine.run(df, strategy)
    print(f"{tf}: {results['total_return']:+.2f}%")
```

## Migration from Existing Strategies

### Before (Old Approach):
```python
# Old: Everything in one file
def calculate_ema(prices, period):
    return prices.ewm(span=period).mean()

def calculate_atr(high, low, close, period):
    # 20 lines of code
    pass

def calculate_rsi(prices, period):
    # 15 lines of code
    pass

class Backtest:
    def __init__(self):
        # All indicators hardcoded
        pass
    
    def run(self):
        # 200 lines of backtest logic
        pass
```

### After (Framework Approach):
```python
# New: Reusable components
from src.indicators import EMA, ATR, RSI
from src.strategies import TrendFollowingStrategy
from src.backtest.engine import BacktestEngine

strategy = TrendFollowingStrategy(config)
engine = BacktestEngine(config)
results = engine.run(df, strategy)
```

**Benefits:**
- 90% less code
- No duplication
- Easy to extend
- Consistent interface
- Production-ready

## Example: Full Workflow

```python
#!/usr/bin/env python3
"""Complete trading framework workflow"""

from src.data.fetcher import DataFetcher
from src.strategies import TrendFollowingStrategy
from src.backtest.engine import BacktestEngine
from src.optimization import BayesianOptimizer
from src.analysis import OverfittingDetector, WalkForwardAnalyzer

# 1. Fetch data
fetcher = DataFetcher(exchange='binance')
df = fetcher.fetch('BTC/USDT', '4h', 730)

# 2. Optimize parameters
optimizer = BayesianOptimizer(
    strategy_class=TrendFollowingStrategy,
    df=df,
    engine_config={'initial_capital': 10000},
    n_trials=100
)
best_config = optimizer.optimize()

# 3. Run backtest with best params
strategy = TrendFollowingStrategy(best_config['best_params'])
engine = BacktestEngine({'initial_capital': 10000})
results = engine.run(df, strategy)

# 4. Check for overfitting
detector = OverfittingDetector()
of_results = detector.analyze(strategy, df, train_pct=0.7)

# 5. Walk-forward analysis
wf_analyzer = WalkForwardAnalyzer()
wf_results = wf_analyzer.analyze(strategy, df, train_size=500, test_size=100)

# 6. Display results
print(f"Return: {results['total_return']:+.2f}%")
print(f"Sharpe: {results['sharpe_ratio']:.2f}")
print(f"Overfitting Decay: {of_results['decay']:.1%}")
print(f"Walk-Forward Return: {wf_results['mean_return']:+.2f}%")
```

## Supported Exchanges

- **Binance**: `exchange='binance'`
- **Coinbase**: `exchange='coinbase'`
- **Kraken**: `exchange='kraken'`
- **Bybit**: `exchange='bybit'`
- **OKX**: `exchange='okx'`
- **KuCoin**: `exchange='kucoin'`

## Supported Timeframes

- Minutes: `1m`, `5m`, `15m`
- Hours: `1h`, `4h`
- Days: `1d`
- Weeks: `1w`
- Months: `1M`

## Available Indicators

| Indicator | Class | Description |
|-----------|-------|-------------|
| EMA | `EMA` | Exponential Moving Average |
| ATR | `ATR` | Average True Range |
| RSI | `RSI` | Relative Strength Index |
| ADX | `ADX` | Average Directional Index |
| Donchian | `Donchian` | Donchian Channels |

## Available Strategies

| Strategy | Description |
|----------|-------------|
| `TrendFollowingStrategy` | EMA pullback entries in trends |
| `PullbackStrategy` | Pullback to EMA/Support levels |
| `BreakoutStrategy` | Donchian channel breakout |

## Configuration Files

Strategy configurations are stored in `config/strategies/`:

```
config/strategies/
├── trend_following_4h.yaml    # 4H trend-following
├── trend_following_1h.yaml    # 1H trend-following
└── breakout.yaml               # Breakout strategy
```

## Performance Metrics

The framework calculates these metrics automatically:

- **Total Return**: Overall percentage return
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Maximum peak-to-trough decline
- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Total profit / Total loss
- **Average Trade**: Mean trade P&L

---

## Analytics Module

Comprehensive analytics, reporting, and visualization for trading strategies.

### Overview

The analytics module eliminates the need for excessive `print()` statements by providing a unified API for:
- **Results Analysis** - Extract insights from backtest results
- **Visualization** - Interactive Plotly charts
- **Reporting** - Export to CSV, HTML, JSON
- **Comparison** - Compare strategies, parameters, assets, or timeframes
- **Console Output** - Formatted summaries without manual printing

### Quick Start

```python
from src.analytics import Analytics
from src.data.fetcher import DataFetcher
from src.strategies.trend_following import TrendFollowingStrategy
from src.backtest.engine import BacktestEngine

# Run backtest
fetcher = DataFetcher(exchange="binance")
df = fetcher.fetch("BTC/USDT", "4h", period_days=365)

config = {
    "ema_fast": 55,
    "ema_slow": 144,
    "atr_period": 14,
    "atr_multiplier_sl": 0.6,
    "atr_multiplier_tp": 2.0,
    "position_size_pct": 0.7,
    "initial_capital": 10000,
}

strategy = TrendFollowingStrategy(config)
engine = BacktestEngine({"initial_capital": 10000})
results = engine.run(df, strategy)

# Create analytics object
buy_hold = fetcher.calculate_buy_and_hold(df)
analytics = Analytics(
    results,
    df=df,
    name="Trend Following (EMA 55/144)",
    config=config,
    buy_hold_results=buy_hold,
)

# Print formatted summary (no print statements needed!)
analytics.print_summary()

# Generate reports
analytics.save_csv("outputs/metrics.csv")
analytics.save_json("outputs/report.json")
analytics.save_html("outputs/report.html")

# Generate plots
analytics.plot_all(output_dir="outputs/plots")
```

### Compare Strategies

```python
from src.analytics import compare_strategies, rank_strategies

# Run multiple strategies
results_dict = {
    "Strategy A": results_a,
    "Strategy B": results_b,
    "Strategy C": results_c,
}

# Compare with table
compare_strategies(results_dict)

# Rank by Sharpe
rank_strategies(results_dict, by="sharpe_ratio")
```


## Dependencies

```bash
uv add pandas numpy ccxt matplotlib seaborn optuna
```

## CLI Scripts

Located in `scripts/`:

```bash
# Run backtest
uv run scripts/run_backtest.py --config config/strategies/trend_following_4h.yaml

# Run optimization
uv run scripts/run_optimization.py --config config/strategies/trend_following_4h.yaml --method bayesian --trials 100

# Run analysis
uv run scripts/run_analysis.py --config config/strategies/trend_following_4h.yaml --type overfitting

# Compare strategies
uv run scripts/compare_strategies.py --configs config/strategies/*.yaml
```

## Best Practices

1. **Always validate on out-of-sample data**
2. **Use train/test split or walk-forward**
3. **Check for overfitting before deployment**
4. **Start with Bayesian optimization** (most efficient)
5. **Use multiple assets/timeframes** for robustness
6. **Document parameter choices** in YAML configs

## Contributing

### Adding New Indicator:
1. Create `src/indicators/my_indicator.py`
2. Inherit from `BaseIndicator`
3. Implement `calculate()` method
4. Add to `src/indicators/__init__.py`

### Adding New Strategy:
1. Create `src/strategies/my_strategy.py`
2. Inherit from `BaseStrategy`
3. Implement required methods
4. Create YAML config in `config/strategies/`

### Adding New Optimizer:
1. Create `src/optimization/my_optimizer.py`
2. Implement `optimize()` method
3. Add to `src/optimization/__init__.py`

## License

MIT
