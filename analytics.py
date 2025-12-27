#!/usr/bin/env python3
"""
Comprehensive Analytics for cryptocurrency 1h data (last 2 years)
Focuses on reliable, statistically significant patterns
"""

import argparse
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def fetch_crypto_data(symbol="BTC/USDT"):
    """Fetch 2 years of cryptocurrency 1h data from Binance"""
    exchange = ccxt.binance()

    end_time = int(datetime.now().timestamp() * 1000)
    start_time = end_time - (2 * 365 * 24 * 60 * 60 * 1000)

    all_ohlcv = []
    current_time = start_time

    while current_time < end_time:
        limit = 1000
        ohlcv = exchange.fetch_ohlcv(
            symbol, timeframe="1h", since=current_time, limit=limit
        )

        if len(ohlcv) == 0:
            break

        all_ohlcv.extend(ohlcv)
        current_time = ohlcv[-1][0] + 1

    if len(all_ohlcv) == 0:
        raise ValueError(f"No data fetched from Binance for {symbol}")

    df = pd.DataFrame(
        all_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)

    return df


def calculate_return_metrics(df):
    """Calculate return statistics"""
    df["return"] = df["close"].pct_change() * 100
    df["candle_color"] = np.where(df["close"] > df["open"], "green", "red")
    df["body_size"] = abs(df["close"] - df["open"]) / df["open"] * 100

    open_max = np.maximum(df["open"], df["close"])
    df["upper_wick"] = (df["high"] - open_max) / df["open"] * 100

    close_min = np.minimum(df["open"], df["close"])
    df["lower_wick"] = (close_min - df["low"]) / df["open"] * 100

    df["range"] = (df["high"] - df["low"]) / df["open"] * 100

    df["true_range"] = (
        np.maximum(
            df["high"] - df["low"],
            np.maximum(
                abs(df["high"] - df["close"].shift(1)),
                abs(df["low"] - df["close"].shift(1)),
            ),
        )
        / df["close"].shift(1)
        * 100
    )

    return df


def analyze_basic_candle_stats(df):
    """Analyze basic candle statistics"""
    total_candles = len(df)
    green_candles = df[df["candle_color"] == "green"]
    red_candles = df[df["candle_color"] == "red"]

    stats = {
        "Total Candles": total_candles,
        "Green Candles": len(green_candles),
        "Red Candles": len(red_candles),
        "Green %": round(len(green_candles) / total_candles * 100, 2),
        "Red %": round(len(red_candles) / total_candles * 100, 2),
        "Avg Green Return %": round(green_candles["return"].mean(), 3),
        "Avg Red Return %": round(red_candles["return"].mean(), 3),
        "Median Green Return %": round(green_candles["return"].median(), 3),
        "Median Red Return %": round(red_candles["return"].median(), 3),
        "Max Green Return %": round(green_candles["return"].max(), 3),
        "Max Red Return %": round(red_candles["return"].min(), 3),
        "Std Dev Green Returns": round(green_candles["return"].std(), 3),
        "Std Dev Red Returns": round(red_candles["return"].std(), 3),
        "Avg Green Body Size %": round(green_candles["body_size"].mean(), 3),
        "Avg Red Body Size %": round(red_candles["body_size"].mean(), 3),
        "Avg Green Upper Wick %": round(green_candles["upper_wick"].mean(), 3),
        "Avg Red Upper Wick %": round(red_candles["upper_wick"].mean(), 3),
        "Avg Green Lower Wick %": round(green_candles["lower_wick"].mean(), 3),
        "Avg Red Lower Wick %": round(red_candles["lower_wick"].mean(), 3),
        "Avg Green Range %": round(green_candles["range"].mean(), 3),
        "Avg Red Range %": round(red_candles["range"].mean(), 3),
    }

    return stats


def analyze_consecutive_patterns(df):
    """Analyze consecutive candle patterns (streaks)"""

    def get_streak_lengths(color):
        streaks = []
        current_streak = 1
        colors = df["candle_color"].tolist()

        for i in range(1, len(colors)):
            if colors[i] == color and colors[i - 1] == color:
                current_streak += 1
            elif colors[i] == color:
                streaks.append(current_streak)
                current_streak = 1
            elif current_streak > 1:
                streaks.append(current_streak)
                current_streak = 1

        if current_streak > 1:
            streaks.append(current_streak)

        return streaks if streaks else [1] if colors[0] == color else []

    green_streaks = get_streak_lengths("green")
    red_streaks = get_streak_lengths("red")

    def analyze_streaks(streaks, name):
        if not streaks:
            return {}
        return {
            f"{name} Streaks Count": len(streaks),
            f"Avg {name} Streak Length": round(np.mean(streaks), 2),
            f"Max {name} Streak Length": max(streaks),
            f"Median {name} Streak Length": round(np.median(streaks), 2),
        }

    stats = {}
    stats.update(analyze_streaks(green_streaks, "Green"))
    stats.update(analyze_streaks(red_streaks, "Red"))

    return stats


def analyze_time_patterns(df):
    """Analyze patterns by time (hour, day of week, month)"""
    df["hour"] = df.index.hour
    df["day_of_week"] = df.index.dayofweek
    df["month"] = df.index.month

    hourly_performance = (
        df.groupby("hour")["return"].agg(["mean", "count", "std"]).round(3)
    )
    daily_performance = (
        df.groupby("day_of_week")["return"].agg(["mean", "count", "std"]).round(3)
    )
    monthly_performance = (
        df.groupby("month")["return"].agg(["mean", "count", "std"]).round(3)
    )

    day_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    daily_performance.index = daily_performance.index.map(lambda x: day_names[x])

    return {
        "hourly_performance": hourly_performance,
        "daily_performance": daily_performance,
        "monthly_performance": monthly_performance,
    }


def analyze_volatility(df):
    """Analyze volatility characteristics"""
    df["rolling_volatility_24h"] = df["return"].rolling(24).std()
    df["rolling_volatility_168h"] = df["return"].rolling(168).std()

    volatility_stats = {
        "Avg ATR (True Range) %": round(df["true_range"].mean(), 3),
        "Median ATR %": round(df["true_range"].median(), 3),
        "Max ATR %": round(df["true_range"].max(), 3),
        "Avg 24h Rolling Volatility": round(df["rolling_volatility_24h"].mean(), 3),
        "Avg 168h (1 week) Rolling Volatility": round(
            df["rolling_volatility_168h"].mean(), 3
        ),
        "Volatility Clustering Index": round(
            df["rolling_volatility_24h"].autocorr(lag=1), 3
        )
        if len(df) > 24
        else "N/A",
    }

    return volatility_stats


def analyze_volume(df):
    """Analyze volume patterns"""
    green_volume = df[df["candle_color"] == "green"]["volume"]
    red_volume = df[df["candle_color"] == "red"]["volume"]

    volume_price_corr = round(df["volume"].corr(df["return"]), 3)

    volume_stats = {
        "Avg Volume (Green Candles)": round(green_volume.mean(), 0),
        "Avg Volume (Red Candles)": round(red_volume.mean(), 0),
        "Volume Difference %": round(
            (green_volume.mean() - red_volume.mean()) / red_volume.mean() * 100, 2
        ),
        "Volume-Return Correlation": volume_price_corr,
        "Total Volume (2 years)": round(df["volume"].sum(), 0),
        "Avg Hourly Volume": round(df["volume"].mean(), 0),
    }

    return volume_stats


def analyze_price_distribution(df):
    """Analyze price distribution and percentiles"""
    price_stats = {
        "Start Price": round(df["close"].iloc[0], 2),
        "End Price": round(df["close"].iloc[-1], 2),
        "Max Price": round(df["high"].max(), 2),
        "Min Price": round(df["low"].min(), 2),
        "Price Range %": round(
            (df["high"].max() - df["low"].min()) / df["low"].min() * 100, 2
        ),
        "25th Percentile": round(df["close"].quantile(0.25), 2),
        "50th Percentile (Median)": round(df["close"].quantile(0.50), 2),
        "75th Percentile": round(df["close"].quantile(0.75), 2),
        "90th Percentile": round(df["close"].quantile(0.90), 2),
        "95th Percentile": round(df["close"].quantile(0.95), 2),
    }

    return price_stats


def analyze_gaps(df):
    """Analyze gap patterns"""
    df["gap_up"] = (df["open"] - df["close"].shift(1)) / df["close"].shift(1) * 100
    df["gap_down"] = (df["close"].shift(1) - df["open"]) / df["close"].shift(1) * 100

    gap_ups = df[df["gap_up"] > 0.1]
    gap_downs = df[df["gap_down"] > 0.1]

    gap_stats = {
        "Gap Up Events (>0.1%)": len(gap_ups),
        "Gap Down Events (>0.1%)": len(gap_downs),
        "Avg Gap Up Size %": round(gap_ups["gap_up"].mean(), 3)
        if len(gap_ups) > 0
        else "N/A",
        "Avg Gap Down Size %": round(gap_downs["gap_down"].mean(), 3)
        if len(gap_downs) > 0
        else "N/A",
        "Max Gap Up %": round(df["gap_up"].max(), 3),
        "Max Gap Down %": round(df["gap_down"].max(), 3),
    }

    return gap_stats


def calculate_risk_metrics(df):
    """Calculate risk metrics"""
    cumulative_returns = (1 + df["return"] / 100).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max * 100

    risk_stats = {
        "Total Return %": round(df["return"].sum(), 2),
        "CAGR %": round(
            ((df["close"].iloc[-1] / df["close"].iloc[0]) ** (1 / (len(df) / 8760)) - 1)
            * 100,
            2,
        ),
        "Max Drawdown %": round(drawdown.min(), 2),
        "Avg Drawdown %": round(drawdown[drawdown < 0].mean(), 2)
        if len(drawdown[drawdown < 0]) > 0
        else "N/A",
        "Std Dev of Returns %": round(df["return"].std(), 3),
        "Skewness": round(df["return"].skew(), 3),
        "Kurtosis": round(df["return"].kurtosis(), 3),
    }

    return risk_stats


def generate_markdown_report(
    df,
    basic_stats,
    consecutive_stats,
    time_patterns,
    volatility_stats,
    volume_stats,
    price_stats,
    gap_stats,
    risk_metrics,
    symbol="BTCUSDT",
):
    """Generate comprehensive markdown report"""

    report = f"""# {symbol} 1H Analytics Report
**Data Period:** {df.index.min().strftime("%Y-%m-%d")} to {df.index.max().strftime("%Y-%m-%d")}
**Total Hours:** {len(df):,}

---

## Executive Summary

- **Price Change:** {price_stats["Start Price"]:,} → {price_stats["End Price"]:,} ({risk_metrics["Total Return %"]:+.2f}%)
- **Green Candles:** {basic_stats["Green Candles"]:,} ({basic_stats["Green %"]}%) | Red Candles: {basic_stats["Red Candles"]:,} ({basic_stats["Red %"]}%)
- **Average Green Return:** {basic_stats["Avg Green Return %"]:.3f}% | Average Red Return: {basic_stats["Avg Red Return %"]:.3f}%
- **Max Drawdown:** {risk_metrics["Max Drawdown %"]}%
- **Volatility (Avg ATR):** {volatility_stats["Avg ATR (True Range) %"]:.3f}%

---

## 1. Basic Candle Statistics

| Metric | Value |
|--------|-------|
| Total Candles | {basic_stats["Total Candles"]:,} |
| Green Candles | {basic_stats["Green Candles"]:,} ({basic_stats["Green %"]}%) |
| Red Candles | {basic_stats["Red Candles"]:,} ({basic_stats["Red %"]}%) |

### Green Candle Returns
| Metric | Value |
|--------|-------|
| Average Return | {basic_stats["Avg Green Return %"]:.3f}% |
| Median Return | {basic_stats["Median Green Return %"]:.3f}% |
| Maximum Return | {basic_stats["Max Green Return %"]:.3f}% |
| Std Dev | {basic_stats["Std Dev Green Returns"]:.3f}% |

### Red Candle Returns
| Metric | Value |
|--------|-------|
| Average Return | {basic_stats["Avg Red Return %"]:.3f}% |
| Median Return | {basic_stats["Median Red Return %"]:.3f}% |
| Maximum Loss | {basic_stats["Max Red Return %"]:.3f}% |
| Std Dev | {basic_stats["Std Dev Red Returns"]:.3f}% |

### Candle Structure
| Metric | Green Candles | Red Candles |
|--------|---------------|-------------|
| Avg Body Size % | {basic_stats["Avg Green Body Size %"]:.3f}% | {basic_stats["Avg Red Body Size %"]:.3f}% |
| Avg Upper Wick % | {basic_stats["Avg Green Upper Wick %"]:.3f}% | {basic_stats["Avg Red Upper Wick %"]:.3f}% |
| Avg Lower Wick % | {basic_stats["Avg Green Lower Wick %"]:.3f}% | {basic_stats["Avg Red Lower Wick %"]:.3f}% |
| Avg Range % | {basic_stats["Avg Green Range %"]:.3f}% | {basic_stats["Avg Red Range %"]:.3f}% |

---

## 2. Consecutive Candle Patterns (Streaks)

"""

    for key, value in consecutive_stats.items():
        report += f"| {key} | {value} |\n"

    report += f"""
---

## 3. Time-Based Patterns

### Hourly Performance (Average Return %)

| Hour (UTC) | Avg Return | Count | Std Dev |
|------------|------------|-------|---------|
"""

    for hour, row in time_patterns["hourly_performance"].iterrows():
        report += f"| {hour:02d}:00 | {row['mean']:+.3f}% | {int(row['count']):,} | {row['std']:.3f}% |\n"

    report += f"""
### Day of Week Performance

| Day | Avg Return | Count | Std Dev |
|-----|------------|-------|---------|
"""

    for day, row in time_patterns["daily_performance"].iterrows():
        report += f"| {day} | {row['mean']:+.3f}% | {int(row['count']):,} | {row['std']:.3f}% |\n"

    report += f"""
### Monthly Performance

| Month | Avg Return | Count | Std Dev |
|-------|------------|-------|---------|
"""

    for month, row in time_patterns["monthly_performance"].iterrows():
        report += f"| {month:02d} | {row['mean']:+.3f}% | {int(row['count']):,} | {row['std']:.3f}% |\n"

    report += f"""
---

## 4. Volatility Analysis

| Metric | Value |
|--------|-------|
| Avg ATR (True Range) % | {volatility_stats["Avg ATR (True Range) %"]:.3f}% |
| Median ATR % | {volatility_stats["Median ATR %"]:.3f}% |
| Max ATR % | {volatility_stats["Max ATR %"]:.3f}% |
| Avg 24h Rolling Volatility | {volatility_stats["Avg 24h Rolling Volatility"]:.3f}% |
| Avg 168h (1 week) Rolling Volatility | {volatility_stats["Avg 168h (1 week) Rolling Volatility"]:.3f}% |
| Volatility Clustering Index | {volatility_stats["Volatility Clustering Index"]} |

---

## 5. Volume Analysis

| Metric | Value |
|--------|-------|
| Avg Volume (Green Candles) | {volume_stats["Avg Volume (Green Candles)"]:,.0f} |
| Avg Volume (Red Candles) | {volume_stats["Avg Volume (Red Candles)"]:,.0f} |
| Volume Difference % | {volume_stats["Volume Difference %"]:+.2f}% |
| Volume-Return Correlation | {volume_stats["Volume-Return Correlation"]:.3f} |
| Total Volume (2 years) | {volume_stats["Total Volume (2 years)"]:,.0f} |
| Avg Hourly Volume | {volume_stats["Avg Hourly Volume"]:,.0f} |

---

## 6. Price Distribution

| Metric | Value |
|--------|-------|
| Start Price | ${price_stats["Start Price"]:,} |
| End Price | ${price_stats["End Price"]:,} |
| Max Price | ${price_stats["Max Price"]:,} |
| Min Price | ${price_stats["Min Price"]:,} |
| Price Range % | {price_stats["Price Range %"]:.2f}% |
| 25th Percentile | ${price_stats["25th Percentile"]:,} |
| 50th Percentile (Median) | ${price_stats["50th Percentile (Median)"]:,} |
| 75th Percentile | ${price_stats["75th Percentile"]:,} |
| 90th Percentile | ${price_stats["90th Percentile"]:,} |
| 95th Percentile | ${price_stats["95th Percentile"]:,} |

---

## 7. Gap Analysis

| Metric | Value |
|--------|-------|
| Gap Up Events (>0.1%) | {gap_stats["Gap Up Events (>0.1%)"]:,} |
| Gap Down Events (>0.1%) | {gap_stats["Gap Down Events (>0.1%)"]:,} |
| Avg Gap Up Size % | {gap_stats["Avg Gap Up Size %"]} |
| Avg Gap Down Size % | {gap_stats["Avg Gap Down Size %"]} |
| Max Gap Up % | {gap_stats["Max Gap Up %"]:.3f}% |
| Max Gap Down % | {gap_stats["Max Gap Down %"]:.3f}% |

---

## 8. Risk Metrics

| Metric | Value |
|--------|-------|
| Total Return % | {risk_metrics["Total Return %"]:+.2f}% |
| CAGR % | {risk_metrics["CAGR %"]:+.2f}% |
| Max Drawdown % | {risk_metrics["Max Drawdown %"]}% |
| Avg Drawdown % | {risk_metrics["Avg Drawdown %"]} |
| Std Dev of Returns % | {risk_metrics["Std Dev of Returns %"]:.3f}% |
| Skewness | {risk_metrics["Skewness"]:.3f} |
| Kurtosis | {risk_metrics["Kurtosis"]:.3f} |

---

## Key Insights

### Market Behavior
- The market is {"slightly bullish" if basic_stats["Green %"] > 50 else "slightly bearish" if basic_stats["Green %"] < 50 else "balanced"} with {basic_stats["Green %"]:.1f}% green candles vs {basic_stats["Red %"]:.1f}% red candles
- Average green candle return ({basic_stats["Avg Green Return %"]:.3f}%) is {abs(basic_stats["Avg Green Return %"] / basic_stats["Avg Red Return %"]):.2f}x {"larger" if abs(basic_stats["Avg Green Return %"]) > abs(basic_stats["Avg Red Return %"]) else "smaller"} than average red candle return ({basic_stats["Avg Red Return %"]:.3f}%)

### Volatility Profile
- Average hourly volatility (ATR): {volatility_stats["Avg ATR (True Range) %"]:.3f}%
- {"Volatility clustering is present" if volatility_stats["Volatility Clustering Index"] != "N/A" and volatility_stats["Volatility Clustering Index"] > 0.3 else "Low volatility clustering detected"} (index: {volatility_stats["Volatility Clustering Index"]})

### Risk Characteristics
- Maximum drawdown of {risk_metrics["Max Drawdown %"]}% occurred over the 2-year period
- Return distribution is {"positively skewed" if risk_metrics["Skewness"] > 0 else "negatively skewed" if risk_metrics["Skewness"] < 0 else "approximately symmetric"} (skewness: {risk_metrics["Skewness"]})
- {"Fat tails present" if risk_metrics["Kurtosis"] > 3 else "Normal tail behavior"} (kurtosis: {risk_metrics["Kurtosis"]})

### Volume Insights
- {"Green candles have higher volume" if volume_stats["Volume Difference %"] > 0 else "Red candles have higher volume"} by {abs(volume_stats["Volume Difference %"]):.2f}%
- Volume-return correlation: {volume_stats["Volume-Return Correlation"]:.3f} ({"positive correlation" if volume_stats["Volume-Return Correlation"] > 0.1 else "weak correlation" if abs(volume_stats["Volume-Return Correlation"]) < 0.1 else "negative correlation"})

---

## Statistical Significance Notes

- All statistics are based on {len(df):,} hourly candles over 2 years
- Time-based patterns may vary across different market cycles
- Past patterns do not guarantee future performance
- Consider regime changes when applying these insights

---

*Report generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    return report


def main(symbol="BTC/USDT", output_file=None):
    """Main function to run comprehensive analytics"""
    symbol_name = symbol.replace("/", "")
    if output_file is None:
        output_file = f"{symbol_name.lower()}_analytics_report.md"

    print(f"Fetching {symbol} 1h data for the last 2 years...")
    df = fetch_crypto_data(symbol)

    print(f"Successfully fetched {len(df):,} hourly candles")
    print(f"Date range: {df.index.min()} to {df.index.max()}")

    print("\nCalculating return metrics...")
    df = calculate_return_metrics(df)

    print("Analyzing patterns...")
    basic_stats = analyze_basic_candle_stats(df)
    consecutive_stats = analyze_consecutive_patterns(df)
    time_patterns = analyze_time_patterns(df)
    volatility_stats = analyze_volatility(df)
    volume_stats = analyze_volume(df)
    price_stats = analyze_price_distribution(df)
    gap_stats = analyze_gaps(df)
    risk_metrics = calculate_risk_metrics(df)

    print("Generating markdown report...")
    report = generate_markdown_report(
        df,
        basic_stats,
        consecutive_stats,
        time_patterns,
        volatility_stats,
        volume_stats,
        price_stats,
        gap_stats,
        risk_metrics,
        symbol_name.upper(),
    )

    with open(output_file, "w") as f:
        f.write(report)

    print(f"\nReport generated successfully: {output_file}")
    print("\nKey Findings:")
    print(f"  - Total Return: {risk_metrics['Total Return %']:+.2f}%")
    print(
        f"  - Green Candles: {basic_stats['Green %']}% | Red Candles: {basic_stats['Red %']}%"
    )
    print(f"  - Max Drawdown: {risk_metrics['Max Drawdown %']}%")
    print(f"  - Avg ATR: {volatility_stats['Avg ATR (True Range) %']:.3f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate analytics report for cryptocurrency"
    )
    parser.add_argument(
        "symbol",
        nargs="?",
        default="BTC/USDT",
        help="Trading symbol (e.g., BTC/USDT, SOL/USDT)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: {symbol}_analytics_report.md)",
    )
    args = parser.parse_args()

    main(symbol=args.symbol.upper(), output_file=args.output)
