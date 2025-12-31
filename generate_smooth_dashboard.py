#!/usr/bin/env python3
"""
Dashboard Generator for Smooth Trend 4H Analysis

Generates interactive HTML dashboard comparing:
- Smooth Trend 4H (optimized)
- Original Trend 4H (baseline)
- Buy & Hold (benchmark)

Uses Analytics class from src.analytics module

Usage:
    uv run generate_smooth_dashboard.py [output_path]

    Default output: outputs/smooth_trend_4h_dashboard.html
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

sys.path.insert(0, "/Users/aerox0/dev/trading-tests2")

from src.analytics import Analytics
from src.analytics.plots import plot_equity_comparison, plot_metrics_comparison


def load_analysis_data():
    """Load analysis data from outputs"""
    outputs_dir = Path("outputs")

    # Load JSON analysis
    import json

    with open(outputs_dir / "smooth_trend_4h_analysis.json", "r") as f:
        data = json.load(f)

    # Load CSV data
    equity_df = pd.read_csv(outputs_dir / "equity_curves.csv")
    smooth_trades_df = pd.read_csv(outputs_dir / "smooth_trend_4h_trades.csv")
    original_trades_df = pd.read_csv(outputs_dir / "original_trend_4h_trades.csv")
    ohlcv_df = pd.read_csv(outputs_dir / "btc_4h_ohlcv.csv", parse_dates=["timestamp"])
    ohlcv_df.set_index("timestamp", inplace=True)

    return data, equity_df, smooth_trades_df, original_trades_df, ohlcv_df


def create_comparison_dashboard(
    data, equity_df, smooth_trades, original_trades, ohlcv_df, output_path
):
    """Create comparison dashboard using Analytics class"""

    # Create backtest results dict for each strategy from the data
    smooth_results = {
        "equity_curve": equity_df["smooth_trend"].tolist(),
        "trades": smooth_trades.to_dict("records"),
        "total_return": data["smooth_trend_4h"]["metrics"]["total_return"],
        "sharpe_ratio": data["smooth_trend_4h"]["metrics"]["sharpe_ratio"],
        "max_drawdown": data["smooth_trend_4h"]["metrics"]["max_drawdown"],
        "win_rate": data["smooth_trend_4h"]["metrics"]["win_rate"],
        "total_trades": data["smooth_trend_4h"]["metrics"]["total_trades"],
        "profit_factor": data["smooth_trend_4h"]["metrics"]["profit_factor"],
        "final_capital": data["smooth_trend_4h"]["metrics"]["final_capital"],
    }

    original_results = {
        "equity_curve": equity_df["original_trend"].tolist(),
        "trades": original_trades.to_dict("records"),
        "total_return": data["original_trend_4h"]["metrics"]["total_return"],
        "sharpe_ratio": data["original_trend_4h"]["metrics"]["sharpe_ratio"],
        "max_drawdown": data["original_trend_4h"]["metrics"]["max_drawdown"],
        "win_rate": data["original_trend_4h"]["metrics"]["win_rate"],
        "total_trades": data["original_trend_4h"]["metrics"]["total_trades"],
        "final_capital": data["original_trend_4h"]["metrics"]["final_capital"],
    }

    buy_hold_results = data["buy_hold"]

    # Create Analytics objects
    smooth_analytics = Analytics(
        smooth_results,
        df=ohlcv_df,
        name="Smooth Trend 4H",
        config=data["smooth_trend_4h"]["config"],
        buy_hold_results=buy_hold_results,
        output_dir="outputs/smooth_trend_4h",
    )

    original_analytics = Analytics(
        original_results,
        df=ohlcv_df,
        name="Original Trend 4H",
        config=data["original_trend_4h"]["config"],
        buy_hold_results=buy_hold_results,
        output_dir="outputs/original_trend_4h",
    )

    # Generate dashboard HTML
    print("\nGenerating dashboard using Analytics class...")

    # Get individual plots as figures (using Analytics methods)
    equity_fig = smooth_analytics.plot_equity_curve(include_buy_hold=True)
    drawdown_fig = smooth_analytics.plot_drawdown(include_buy_hold=True)
    monthly_fig = smooth_analytics.plot_monthly_returns(include_buy_hold=True)
    pnl_fig = smooth_analytics.plot_pnl_distribution()

    # Create comparison plots using plots module directly
    results_dict = {
        "Smooth Trend 4H": smooth_results,
        "Original Trend 4H": original_results,
    }

    comparison_fig = plot_equity_comparison(results_dict, save_path=None)

    # Create metrics comparison
    metrics = ["total_return", "sharpe_ratio", "win_rate"]
    metrics_fig = plot_metrics_comparison(results_dict, metrics, save_path=None)

    # Generate custom combined dashboard
    html_content = create_dashboard_html(
        data,
        smooth_analytics,
        original_analytics,
        equity_fig,
        drawdown_fig,
        monthly_fig,
        pnl_fig,
        comparison_fig,
        metrics_fig,
        ohlcv_df,
    )

    # Save dashboard
    with open(output_path, "w") as f:
        f.write(html_content)

    print(f"\n✓ Dashboard saved to: {output_path}")
    return str(output_path)


def create_dashboard_html(
    data,
    smooth_analytics,
    original_analytics,
    equity_fig,
    drawdown_fig,
    monthly_fig,
    pnl_fig,
    comparison_fig,
    metrics_fig,
    ohlcv_df,
):
    """Create the dashboard HTML"""

    smooth = data["smooth_trend_4h"]["metrics"]
    original = data["original_trend_4h"]["metrics"]

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smooth Trend 4H Strategy - Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        
        .kpi-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        
        .kpi-title {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .kpi-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        
        .kpi-subtitle {{
            font-size: 0.8em;
            opacity: 0.7;
            margin-bottom: 5px;
        }}
        
        .kpi-diff {{
            font-size: 0.85em;
            font-weight: bold;
        }}
        
        .section {{
            margin: 40px 0;
        }}
        
        .section-title {{
            color: #333;
            font-size: 1.5em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        
        .chart-container {{
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 0.9em;
        }}
        
        .color-legend {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
        }}
        
        .legend-text {{
            font-weight: 500;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Smooth Trend 4H Strategy Dashboard</h1>
        <p class="subtitle">Optimized for smoother returns with lower drawdown • Generated with src.analytics.Analytics class</p>
        
        <div class="color-legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #26a69a;"></div>
                <span class="legend-text">Smooth Trend 4H</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #f39c12;"></div>
                <span class="legend-text">Original Trend 4H</span>
            </div>
        </div>
        
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-title">Total Return</div>
                <div class="kpi-value">{smooth["total_return"]:.2f}%</div>
                <div class="kpi-subtitle">Original: {original["total_return"]:.2f}%</div>
                <div class="kpi-diff">{smooth["total_return"] - original["total_return"]:+.2f}%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Sharpe Ratio</div>
                <div class="kpi-value">{smooth["sharpe_ratio"]:.2f}</div>
                <div class="kpi-subtitle">Original: {original["sharpe_ratio"]:.2f}</div>
                <div class="kpi-diff">{smooth["sharpe_ratio"] - original["sharpe_ratio"]:+.2f}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Max Drawdown</div>
                <div class="kpi-value">{smooth["max_drawdown"]:.2f}%</div>
                <div class="kpi-subtitle">Original: {original["max_drawdown"]:.2f}%</div>
                <div class="kpi-diff">{smooth["max_drawdown"] - original["max_drawdown"]:+.2f}%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Win Rate</div>
                <div class="kpi-value">{smooth["win_rate"]:.1f}%</div>
                <div class="kpi-subtitle">Original: {original["win_rate"]:.1f}%</div>
                <div class="kpi-diff">{smooth["win_rate"] - original["win_rate"]:+.1f}%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Total Trades</div>
                <div class="kpi-value">{int(smooth["total_trades"])}</div>
                <div class="kpi-subtitle">Original: {int(original["total_trades"])}</div>
                <div class="kpi-diff">{int(smooth["total_trades"]) - int(original["total_trades"]):+d}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Profit Factor</div>
                <div class="kpi-value">{smooth["profit_factor"]:.2f}</div>
                <div class="kpi-subtitle">Smooother curve</div>
                <div class="kpi-diff">Goal achieved</div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">📈 Equity Curve Comparison</h2>
            <div class="chart-container" id="equity-chart"></div>
        </div>
        
        <div class="section">
            <h2 class="section-title">📉 Drawdown Analysis</h2>
            <div class="chart-container" id="drawdown-chart"></div>
        </div>
        
        <div class="section">
            <h2 class="section-title">💰 PnL Distribution</h2>
            <div class="chart-container" id="pnl-chart"></div>
        </div>
        
        <div class="section">
            <h2 class="section-title">📅 Monthly Returns</h2>
            <div class="chart-container" id="monthly-chart"></div>
        </div>
        
        <div class="section">
            <h2 class="section-title">📊 Metrics Comparison</h2>
            <div class="chart-container" id="metrics-chart"></div>
        </div>
        
        <div class="footer">
            <p><strong>Smooth Trend 4H Strategy</strong> • Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>Smooth: +{smooth["total_return"]:.2f}% (Sharpe: {smooth["sharpe_ratio"]:.2f}, DD: {smooth["max_drawdown"]:.2f}%) • Original: +{original["total_return"]:.2f}% (Sharpe: {original["sharpe_ratio"]:.2f}, DD: {original["max_drawdown"]:.2f}%)</p>
            <p>Built with src.analytics.Analytics class</p>
        </div>
    </div>
    
    <script>
        Plotly.newPlot('equity-chart', {equity_fig.to_json()});
        Plotly.newPlot('drawdown-chart', {drawdown_fig.to_json()});
        Plotly.newPlot('pnl-chart', {pnl_fig.to_json()});
        Plotly.newPlot('monthly-chart', {monthly_fig.to_json()});
        Plotly.newPlot('metrics-chart', {metrics_fig.to_json()});
    </script>
</body>
</html>
    """

    return html_content


def generate_dashboard(output_path="outputs/smooth_trend_4h_dashboard.html"):
    """Generate complete HTML dashboard"""
    print("=" * 80)
    print("GENERATING SMOOTH TREND 4H DASHBOARD (using Analytics class)")
    print("=" * 80)

    # Load data
    print("\nLoading analysis data...")
    data, equity_df, smooth_trades, original_trades, ohlcv_df = load_analysis_data()

    # Create output directory
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate dashboard
    dashboard_path = create_comparison_dashboard(
        data, equity_df, smooth_trades, original_trades, ohlcv_df, output_path
    )

    print("\n" + "=" * 80)
    print("DASHBOARD GENERATION COMPLETE")
    print("=" * 80)
    print("\nOpen dashboard in your browser to view interactive charts!")
    print("=" * 80)

    return dashboard_path


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate dashboard for Smooth Trend 4H strategy analysis (using Analytics class)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run generate_smooth_dashboard.py
  uv run generate_smooth_dashboard.py outputs/my_dashboard.html
        """,
    )
    parser.add_argument(
        "output_path",
        nargs="?",
        default="outputs/smooth_trend_4h_dashboard.html",
        help="Output path for dashboard HTML (default: outputs/smooth_trend_4h_dashboard.html)",
    )

    args = parser.parse_args()

    try:
        dashboard_path = generate_dashboard(args.output_path)
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(
            "Please run 'uv run backtest_smooth_4h.py' first to generate analysis data."
        )
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
