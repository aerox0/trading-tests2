# Overfitting Analysis Results

## Test Date
December 28, 2025

## Strategy Configuration
- **EMA Fast**: 55
- **EMA Slow**: 144
- **ATR Period**: 14
- **Stop Loss**: 0.6 × ATR
- **Take Profit**: 2.5 × ATR
- **RSI Period**: 14
- **Volume Multiplier**: 1.0
- **Position Size**: 70%

## Overall Performance (Full Dataset)
- **Return**: +41.35%
- **Trades**: 158
- **Win Rate**: 30.4%

---

## Overfitting Test Results

### 1. Train/Test Split (70%/30%)
**Status: ✗ OVERFITTING**

| Metric | Train (In-Sample) | Test (Out-of-Sample) | Decay |
|--------|------------------|---------------------|-------|
| Return | +33.94% | +11.51% | **-66.1%** |
| Trades | 0 | 0 | - |

**Analysis**: Major performance drop on test data. Strategy may be overfitted to training period.

---

### 2. Walk-Forward Analysis
**Status: ✗ OVERFITTING**

- **Average Train Return**: +5.04%
- **Average Test Return**: +1.25%
- **Decay Factor**: **24.9%**

**Analysis**: Strategy performs 4x worse on out-of-sample data in walk-forward testing. This is a strong overfitting signal.

---

### 3. Parameter Sensitivity Analysis
**Status: ⚠ MODERATE**

| Parameter | Variation | Return Change |
|-----------|-----------|--------------|
| ATR SL Multiplier | 0.48 (20% decrease) | **-19.73%** |
| ATR Period | 16 (14% increase) | -10.08% |
| EMA Slow | 115 (20% decrease) | -9.10% |
| ATR Period | 11 (21% decrease) | +6.25% |
| EMA Fast | 44 (20% decrease) | +9.18% |

**Analysis**: Some parameters (especially ATR SL multiplier) are highly sensitive. Small changes cause large performance variations.

---

### 4. Monte Carlo Bootstrap (50 Simulations)
**Status: ⚠ MODERATE**

| Metric | Mean | Std | Min | Max |
|--------|------|-----|-----|-----|
| Return | +18.63% | 18.58% | -11.78% | +55.32% |
| Sharpe | 0.00 | 0.00 | 0.00 | 0.00 |

**Coefficient of Variation: 1.00 (High)**

**Analysis**: High variation across resampled data. Strategy results are not stable.

---

## Overall Assessment

### ✗ **OVERFITTING DETECTED**

**Multiple indicators of overfitting:**
1. Walk-forward decay factor: 24.9% (should be > 60%)
2. Train/test split decay: 33.9% (should be > 70%)
3. Monte Carlo CV: 1.00 (should be < 0.5)
4. Parameter sensitivity: Moderate concern with ATR SL

### Root Causes

1. **Grid search optimizes on Total Return** instead of Sharpe Ratio
   - Total return is easily overfitted to specific market conditions
   - Should optimize on risk-adjusted metrics (Sharpe, Sortino)

2. **No train/test split during optimization**
   - Grid search tests on entire dataset
   - No out-of-sample validation during parameter selection

3. **Parameter space too large** (8 parameters)
   - 4,374 combinations tested on limited data (2 years)
   - Risk of finding "lucky" parameter combinations

4. **Specific market conditions**
   - Tested period (Dec 2023 - Dec 2025) was unusual for crypto
   - Parameters may not generalize to different market regimes

---

## Recommendations

### Immediate Actions

1. **Re-run grid search with train/test split**
   - Use 70% for optimization, 30% for validation
   - Only accept parameters that pass out-of-sample test

2. **Optimize on Sharpe Ratio, not Return**
   ```python
   # Change optimization metric from:
   result["total_return"]
   # To:
   result["sharpe_ratio"]
   ```

3. **Reduce parameter space**
   - Fix ATR period at 14 (widely accepted)
   - Fix RSI period at 14 (standard value)
   - Only optimize EMA periods and multipliers

4. **Test multiple "good" parameters**
   - Don't just use single best result
   - Use ensemble of top 5-10 parameter sets
   - Average results for more robust performance

### Long-term Improvements

5. **Implement walk-forward optimization**
   - Continuously re-optimize on rolling windows
   - More realistic trading simulation

6. **Use cross-validation**
   - K-fold cross-validation on time series data
   - More robust than single train/test split

7. **Collect more data**
   - 2 years is insufficient for 8-parameter optimization
   - Consider using daily data for longer history

8. **Regime detection**
   - Detect bull/bear/sideways markets
   - Use different parameters for different regimes

---

## Conclusion

**Current strategy is likely overfitted** to the tested 2-year period. While it shows good performance (+41.35% on full dataset), the overfitting tests indicate this may not generalize.

**Recommended Next Steps:**
1. Use `overfitting_analysis.py` to test any new parameter sets
2. Prefer simpler parameters with less sensitivity
3. Consider using broader parameter ranges (e.g., EMA 50-200, not just 55/144)
4. Validate on multiple time periods (different years, different assets)
5. Don't expect real trading performance to match backtest results

**Disclaimer:** This analysis is based on historical data and does not guarantee future results. Always use proper risk management and position sizing in live trading.
