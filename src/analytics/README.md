# Analytics Module

Comprehensive analytics, reporting, and visualization for trading strategies.

---

## Overview

The analytics module eliminates the need for excessive `print()` statements by providing a unified API for:
- **Results Analysis** - Extract insights from backtest results
- **Visualization** - Interactive Plotly charts
- **Reporting** - Export to CSV, HTML, JSON
- **Comparison** - Compare strategies/parameters/assets/timeframes
- **Console Output** - Formatted summaries without manual printing

---

## Quick Start

### Basic Usage

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

# Generate all reports
analytics.save_csv("outputs/metrics.csv")
analytics.save_json("outputs/report.json")
analytics.save_html("outputs/report.html")

# Generate all plots
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

---

## Core Components

### 1. Analytics Class

High-level API for single strategy analysis.

**Key Methods:**
- `print_summary()` - Print formatted summary to console
- `analyze()` - Get complete analysis dictionary
- `get_trades_df()` - Get trades as DataFrame
- `get_monthly_returns()` - Get monthly performance
- `get_drawdown_series()` - Get drawdown data

**Reporting:**
- `save_csv(path)` - Export to CSV
- `save_json(path)` - Export to JSON
- `save_html(path)` - Generate HTML dashboard
- `generate_summary()` - Get text summary

**Visualization:**
- `plot_all(output_dir)` - Generate all standard plots
- `plot_equity_curve(save_path)` - Equity curve chart
- `plot_drawdown(save_path)` - Underwater plot
- `plot_monthly_returns(save_path)` - Monthly returns heatmap
- `plot_pnl_distribution(save_path)` - Trade PnL histogram
- `plot_trade_timeline(save_path)` - Trade markers on price chart

### 2. Strategy Comparator

Compare multiple strategies, parameters, assets, or timeframes.

**Key Methods:**
- `add_result(name, results, df, config)` - Add strategy results
- `compare(metrics)` - Comparison table
- `rank(by)` - Rank strategies by metric
- `plot_comparison(save_path)` - Equity curve comparison
- `plot_radar_chart(metrics, save_path)` - Multi-metric radar chart
- `plot_metrics_comparison(metrics, save_path)` - Bar chart comparison
- `save_comparison_report(output_dir)` - Generate full comparison reports

### 3. Metrics Module

Advanced performance metrics (beyond basic strategy metrics).

**Key Metrics:**
- **Calmar Ratio** - Annual return / max drawdown
- **Sortino Ratio** - Downside risk-adjusted return
- **Omega Ratio** - Probability-weighted gains vs losses
- **Win/Loss Streaks** - Maximum consecutive wins/losses
- **Monthly Returns** - Period-by-period performance
- **Profit Distribution** - Avg win/loss, largest win/loss
- **Annualized Metrics** - Annualized return and volatility

### 4. Visualization Module

Interactive Plotly charts.

**Available Plots:**
- `plot_equity_curve()` - Strategy equity over time
- `plot_drawdown()` - Drawdown underwater chart
- `plot_monthly_returns()` - Monthly returns heatmap
- `plot_pnl_distribution()` - Trade PnL histogram
- `plot_equity_comparison()` - Multiple equity curves
- `plot_radar_chart()` - Multi-metric comparison
- `plot_metrics_comparison()` - Bar chart comparison
- `plot_trade_timeline()` - Trade entry/exit markers

### 5. Report Generator

Export results in multiple formats.

**Features:**
- **CSV** - Machine-readable trade logs and metrics
- **JSON** - API-friendly structured data
- **HTML** - Interactive dashboard with Plotly charts

**HTML Dashboard Includes:**
- Performance metrics grid
- Strategy configuration table
- Buy & Hold comparison
- Key insights (auto-generated)
- Download links for CSV/JSON
- Responsive, print-friendly design

---

## Examples

See `examples/example_analytics.py` for complete examples of:
1. Basic analytics with reports
2. Individual plot generation
3. Strategy comparison
4. Parameter variation comparison
5. Full comparison reports

Run examples:
```bash
# Run all examples
uv run examples/example_analytics.py

# Outputs generated in 'outputs/' directory:
# - CSV reports
# - HTML dashboards (open in browser!)
# - Interactive Plotly charts
# - Comparison reports
```

---

## Metrics Explained

### Key Metrics (Crucial, No Noise)

**Performance:**
- **Total Return** - Overall profitability
- **Sharpe Ratio** - Risk-adjusted return (most important)
- **Annualized Return** - Yearly return rate
- **Calmar Ratio** - Return relative to drawdown

**Risk:**
- **Max Drawdown** - Largest peak-to-trough decline
- **Sortino Ratio** - Downside risk focus
- **Annualized Volatility** - Price fluctuation

**Trading:**
- **Win Rate** - Percentage of winning trades
- **Profit Factor** - Gross profit / gross loss
- **Total Trades** - Number of trades executed

**Win/Loss:**
- **Average Win** - Mean of winning trades
- **Average Loss** - Mean of losing trades
- **Largest Win** - Best trade
- **Largest Loss** - Worst trade
- **Max Win/Loss Streak** - Longest consecutive runs

### Auto-Generated Insights

Analytics module automatically generates insights about:
- Overall profitability
- Risk-adjusted performance quality
- Drawdown severity and risk management
- Win rate vs profit factor balance
- Trading frequency (statistical significance)

---

## Use Cases

### 1. Compare Different Strategies
```python
results_dict = {
    "Trend Following": results_trend,
    "Pullback": results_pullback,
    "Breakout": results_breakout,
}
compare_strategies(results_dict)
```

### 2. Compare Parameter Variations
```python
for sl_mult in [0.5, 0.6, 0.7, 0.8]:
    config["atr_multiplier_sl"] = sl_mult
    # Run backtest
    results_dict[f"SL {sl_mult}"] = results

compare_strategies(results_dict)
```

### 3. Compare Different Assets
```python
for symbol in ["BTC/USDT", "ETH/USDT", "SOL/USDT"]:
    df = fetcher.fetch(symbol, "4h", period_days=365)
    results_dict[symbol] = engine.run(df, strategy)

compare_strategies(results_dict)
```

### 4. Compare Different Timeframes
```python
for timeframe in ["1h", "4h", "1d"]:
    df = fetcher.fetch("BTC/USDT", timeframe, period_days=365)
    results_dict[timeframe] = engine.run(df, strategy)

compare_strategies(results_dict)
```

---

## Export Formats

### CSV
- `metrics.csv` - Summary metrics
- `{strategy}_trades.csv` - Trade log
- `{strategy}_equity.csv` - Equity curve data

### JSON
- `{strategy}_report.json` - Complete structured data
- Includes metrics, trades summary, configuration

### HTML
- `{strategy}_report.html` - Interactive dashboard
- Comparison reports with all strategies
- Open in browser for interactive charts

---

## Data-Heavy Dashboard

HTML reports focus on **crucial information only**:

**Performance Metrics Grid:**
- Total Return (color-coded: green/profit, red/loss)
- Sharpe Ratio
- Max Drawdown
- Win Rate
- Final Capital

**Configuration Section:**
- Strategy parameters used
- Easy to reproduce

**Buy & Hold Comparison:**
- Strategy return vs benchmark
- Performance difference

**Download Links:**
- CSV download
- JSON download

**Interactive Charts:**
- Equity curve (zoomable)
- Drawdown chart
- Monthly returns heatmap
- PnL distribution

**No Noise:**
- Only essential metrics shown
- Clear visual hierarchy
- Professional, data-heavy design
- Print-friendly

---

## Advantages

### 1. No More Print Statements
```python
# OLD WAY
print(f"Total Return: {results['total_return']:+.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
# ... many more print statements

# NEW WAY
analytics.print_summary()  # One line!
```

### 2. Interactive Visualization
- Plotly charts: zoom, pan, hover
- Better than static Matplotlib charts
- Shareable (HTML files)

### 3. Easy Comparison
```python
# Compare anything easily
compare_strategies(results_dict)
rank_strategies(results_dict, by="sharpe_ratio")
generate_comparison_reports(results_dict)
```

### 4. Multiple Export Formats
- CSV for Excel/spreadsheets
- JSON for APIs/automation
- HTML for reports/presentation

### 5. Consistent API
- Same methods for all analyses
- Learn once, use everywhere

---

## Module Structure

```
src/analytics/
├── __init__.py          # Main API (Analytics class)
├── analyzer.py          # Results analysis & insights
├── plots.py             # Plotly visualization
├── reports.py           # CSV/HTML/JSON generation
├── comparator.py         # Multi-strategy comparison
├── metrics.py           # Advanced metrics
└── utils.py             # Helper functions
```

---

## Dependencies

Required (already in project):
- `plotly>=6.5.0` - Interactive charts

Used by framework:
- `pandas` - Data manipulation
- `numpy` - Numerical calculations

---

## Migration from Old Code

### Before (Many Print Statements)
```python
print("=" * 80)
print("BACKTEST RESULTS")
print("=" * 80)
print(f"Total Return: {results['total_return']:+.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
# ... many more lines
```

### After (One Line)
```python
analytics = Analytics(results, df=df, name="Strategy")
analytics.print_summary()  # Everything formatted!
```

---

## Next Steps

1. **Run Examples** - Try `examples/example_analytics.py`
2. **Integrate into Workflow** - Use Analytics instead of prints
3. **Generate Reports** - CSV/HTML for documentation
4. **Compare Strategies** - Use Comparator for analysis
5. **Share Dashboards** - HTML reports are presentation-ready

---

The analytics module provides **everything you need** to analyze, visualize, and compare trading strategies without any manual work.
