"""Report generation in CSV, HTML, JSON formats"""

import json
import pandas as pd
from typing import Dict, Any, Optional
from pathlib import Path
import plotly.graph_objects as go


class ReportGenerator:
    """Generate reports in multiple formats"""

    def __init__(
        self,
        results: Dict[str, Any],
        strategy_name: str = "Strategy",
        config: Optional[Dict] = None,
        buy_hold_results: Optional[Dict] = None,
    ):
        """Initialize report generator

        Args:
            results: Backtest results dictionary
            strategy_name: Strategy name
            config: Strategy configuration (optional)
            buy_hold_results: Buy & Hold baseline results (optional)
        """
        self.results = results
        self.name = strategy_name
        self.config = config or {}
        self.buy_hold = buy_hold_results

    def to_csv(
        self, path: str, include_trades: bool = True, include_equity: bool = False
    ):
        """Export results to CSV

        Args:
            path: Output CSV path
            include_trades: Include trade log
            include_equity: Include equity curve
        """
        export_data = {}

        metrics_list = []

        timeframe = self.config.get("timeframe", "N/A")
        date_range = self.config.get("date_range", "N/A")

        metrics_list.append({"metric": "Timeframe", "value": timeframe})
        metrics_list.append({"metric": "Date Range", "value": date_range})
        metrics_list.append({"metric": "", "value": ""})

        metrics_list.append(
            {
                "metric": "Total Return",
                "value": f"{self.results.get('total_return', 0):.2f}%",
            }
        )
        metrics_list.append(
            {
                "metric": "Sharpe Ratio",
                "value": f"{self.results.get('sharpe_ratio', 0):.2f}",
            }
        )
        metrics_list.append(
            {
                "metric": "Max Drawdown",
                "value": f"{self.results.get('max_drawdown', 0):.2f}%",
            }
        )
        metrics_list.append(
            {
                "metric": "Total Trades",
                "value": self.results.get("total_trades", 0),
            }
        )
        metrics_list.append(
            {
                "metric": "Win Rate",
                "value": f"{self.results.get('win_rate', 0):.1f}%",
            }
        )
        metrics_list.append(
            {
                "metric": "Final Capital",
                "value": f"${self.results.get('final_capital', 0):,.2f}",
            }
        )
        metrics_list.append(
            {
                "metric": "Profit Factor",
                "value": f"{self.results.get('profit_factor', 0):.2f}",
            }
        )
        metrics_list.append(
            {
                "metric": "Average Trade",
                "value": f"${self.results.get('avg_trade', 0):.2f}",
            }
        )

        metrics_df = pd.DataFrame(metrics_list)

        export_data["metrics"] = metrics_df

        # Trades log
        if include_trades:
            trades = self.results.get("trades", [])
            if trades:
                trades_df = pd.DataFrame(trades)
                export_data["trades"] = trades_df

        # Equity curve
        if include_equity:
            equity_curve = self.results.get("equity_curve", [])
            if equity_curve:
                equity_df = pd.DataFrame({"equity": equity_curve})
                export_data["equity"] = equity_df

        # Save all sheets
        output_path = Path(path)
        if output_path.suffix.lower() != ".csv":
            output_path = str(output_path) + ".csv"

        # Save metrics
        metrics_df.to_csv(output_path, index=False, mode="w", header=True)

        # If multiple sheets, save with different filenames
        if include_trades and "trades" in export_data:
            trades_path = str(output_path).replace(".csv", "_trades.csv")
            export_data["trades"].to_csv(trades_path, index=False)

        if include_equity and "equity" in export_data:
            equity_path = str(output_path).replace(".csv", "_equity.csv")
            export_data["equity"].to_csv(equity_path, index=False)

        print(f"Saved CSV report to {output_path}")

    def to_json(self, path: str):
        """Export results to JSON

        Args:
            path: Output JSON path
        """
        export_data = {
            "strategy_name": self.name,
            "configuration": self.config,
            "results": {
                k: v
                for k, v in self.results.items()
                if k not in ["equity_curve", "trades"]
            },
            "trades_count": len(self.results.get("trades", [])),
        }

        # Add trades
        if "trades" in self.results:
            export_data["trades"] = self.results["trades"]

        # Add equity curve summary
        if "equity_curve" in self.results:
            ec = self.results["equity_curve"]
            export_data["equity_summary"] = {
                "initial": ec[0] if ec else 0,
                "final": ec[-1] if ec else 0,
                "min": min(ec) if ec else 0,
                "max": max(ec) if ec else 0,
            }

        # Add buy & hold comparison
        if self.buy_hold:
            export_data["buy_hold_baseline"] = {
                "return_pct": self.buy_hold.get("total_return_pct", 0),
                "sharpe_ratio": self.buy_hold.get("sharpe_ratio", 0),
                "max_drawdown_pct": self.buy_hold.get("max_drawdown_pct", 0),
                "difference": self.results.get("total_return", 0)
                - self.buy_hold.get("total_return_pct", 0),
            }

        output_path = Path(path)
        if output_path.suffix.lower() != ".json":
            output_path = str(output_path) + ".json"

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        print(f"Saved JSON report to {output_path}")

    def to_html(self, path: str, template_path: Optional[str] = None):
        """Generate HTML report

        Args:
            path: Output HTML path
            template_path: Custom template path (optional)
        """
        if template_path is None:
            html_content = self._generate_html_report()
        else:
            html_content = self._render_template(template_path)

        output_path = Path(path)
        if output_path.suffix.lower() != ".html":
            output_path = str(output_path) + ".html"

        with open(output_path, "w") as f:
            f.write(html_content)

        print(f"Saved HTML report to {output_path}")

    def _generate_html_report(self) -> str:
        """Generate HTML report string

        Returns:
            HTML content string
        """
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.name} - Strategy Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #1a1a1a; color: white; padding: 30px; border-radius: 8px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; font-size: 32px; }}
        .header .subtitle {{ margin-top: 10px; opacity: 0.8; font-size: 16px; }}
        .section {{ background: white; padding: 30px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .section h2 {{ margin-top: 0; color: #1a1a1a; font-size: 24px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #26a69a; }}
        .metric-label {{ font-size: 12px; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; }}
        .metric-value {{ font-size: 28px; font-weight: bold; color: #1a1a1a; margin-top: 5px; }}
        .metric-value.positive {{ color: #28a745; }}
        .metric-value.negative {{ color: #dc3545; }}
        .config-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .config-table th, .config-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        .config-table th {{ background: #f8f9fa; font-weight: 600; }}
        .insights-list {{ margin-top: 20px; }}
        .insights-list li {{ padding: 12px 0; border-bottom: 1px solid #e9ecef; list-style: none; }}
        .insights-list li:before {{ content: "•"; color: #26a69a; font-weight: bold; margin-right: 10px; }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        .download-section {{ background: #e9ecef; padding: 20px; border-radius: 6px; margin-top: 20px; }}
        .download-section h3 {{ margin-top: 0; }}
        .btn {{ display: inline-block; padding: 12px 24px; background: #26a69a; color: white; text-decoration: none; border-radius: 4px; margin-right: 10px; margin-bottom: 10px; }}
        .btn:hover {{ background: #1e7e85; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self.name}</h1>
            <div class="subtitle">Trading Strategy Performance Report</div>
        </div>

        <div class="section">
            <h2>Performance Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Total Return</div>
                    <div class="metric-value {self._get_value_class("total_return")}">{self.results.get("total_return", 0):+.2f}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Sharpe Ratio</div>
                    <div class="metric-value">{self.results.get("sharpe_ratio", 0):.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Max Drawdown</div>
                    <div class="metric-value negative">{self.results.get("max_drawdown", 0):.2f}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Trades</div>
                    <div class="metric-value">{self.results.get("total_trades", 0)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Win Rate</div>
                    <div class="metric-value">{self.results.get("win_rate", 0):.1f}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Final Capital</div>
                    <div class="metric-value ${self.results.get("final_capital", 0):,.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Profit Factor</div>
                    <div class="metric-value">{self.results.get("profit_factor", 0):.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Average Trade</div>
                    <div class="metric-value ${self.results.get("avg_trade", 0):.2f}</div>
                </div>
            </div>
        </div>
"""

        # Add buy & hold comparison if available
        if self.buy_hold:
            html += f"""
        <div class="section">
            <h2>Buy & Hold Comparison</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Strategy Return</div>
                    <div class="metric-value {self._get_value_class("total_return")}">{self.results.get("total_return", 0):+.2f}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Buy & Hold Return</div>
                    <div class="metric-value {self._get_bh_value_class()}">{self.buy_hold.get("total_return_pct", 0):+.2f}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Difference</div>
                    <div class="metric-value {self._get_diff_value_class()}">{self.results.get("total_return", 0) - self.buy_hold.get("total_return_pct", 0):+.2f}%</div>
                </div>
            </div>
        </div>
"""

        # Add configuration section
        if self.config:
            html += """
        <div class="section">
            <h2>Strategy Configuration</h2>
            <table class="config-table">
                <thead>
                    <tr><th>Parameter</th><th>Value</th></tr>
                </thead>
                <tbody>
"""
            for key, value in self.config.items():
                html += f"                    <tr><td>{key}</td><td>{value}</td></tr>\n"
            html += """
                </tbody>
            </table>
        </div>
"""

        # Add downloads section
        html += """
        <div class="download-section">
            <h3>Download Data</h3>
            <p>Raw data files (save report to include these files):</p>
            <div>
                <a href="#" class="btn">Download CSV</a>
                <a href="#" class="btn">Download JSON</a>
            </div>
        </div>

    </div>
</body>
</html>
"""
        return html

    def _get_value_class(self, metric: str) -> str:
        """Get CSS class based on metric value

        Args:
            metric: Metric name

        Returns:
            CSS class string
        """
        value = self.results.get(metric, 0)
        if metric in ["total_return", "sharpe_ratio", "win_rate", "profit_factor"]:
            return "positive" if value > 0 else ""
        return ""

    def _get_bh_value_class(self) -> str:
        """Get CSS class for buy & hold value

        Returns:
            CSS class string
        """
        if not self.buy_hold:
            return ""
        value = self.buy_hold.get("total_return_pct", 0)
        return "positive" if value > 0 else ""

    def _get_diff_value_class(self) -> str:
        """Get CSS class for difference value

        Returns:
            CSS class string
        """
        if not self.buy_hold:
            return ""
        diff = self.results.get("total_return", 0) - self.buy_hold.get(
            "total_return_pct", 0
        )
        return "positive" if diff > 0 else "negative"

    def _render_template(self, template_path: str) -> str:
        """Render custom template

        Args:
            template_path: Path to template file

        Returns:
            Rendered HTML string
        """
        try:
            with open(template_path, "r") as f:
                template = f.read()

            # Simple template rendering (in production, use Jinja2)
            html = template.replace("{{ strategy_name }}", self.name)
            html = html.replace(
                "{{ total_return }}", f"{self.results.get('total_return', 0):.2f}%"
            )

            return html
        except Exception as e:
            print(f"Error rendering template: {e}")
            return self._generate_html_report()

    def _generate_html_report_with_charts(
        self,
        results: Dict[str, Any],
        df: Optional[pd.DataFrame],
        name: str,
        config: Dict,
    ) -> str:
        """Generate HTML report with iframes to plot files

        Args:
            results: Backtest results
            df: OHLCV DataFrame
            name: Strategy name
            config: Strategy config

        Returns:
            HTML string with iframes to plot files
        """

        timeframe = config.get("timeframe", "N/A")
        date_range = config.get("date_range", "N/A")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #1a1a1a; color: white; padding: 30px; border-radius: 8px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; font-size: 32px; }}
        .header .subtitle {{ margin-top: 10px; opacity: 0.8; font-size: 16px; }}
        .header .meta {{ margin-top: 15px; display: flex; gap: 30px; }}
        .header .meta-item {{ display: flex; flex-direction: column; }}
        .header .meta-label {{ font-size: 11px; opacity: 0.6; text-transform: uppercase; letter-spacing: 0.5px; }}
        .header .meta-value {{ font-size: 14px; font-weight: 500; }}
        .section {{ background: white; padding: 30px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .section h2 {{ margin-top: 0; color: #1a1a1a; font-size: 24px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #26a69a; }}
        .metric-label {{ font-size: 12px; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; }}
        .metric-value {{ font-size: 28px; font-weight: bold; color: #1a1a1a; margin-top: 5px; }}
        .metric-value.positive {{ color: #28a745; }}
        .metric-value.negative {{ color: #dc3545; }}
        .config-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .config-table th, .config-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        .config-table th {{ background: #f8f9fa; font-weight: 600; }}
        .config-table tr.highlight {{ background: #e7f3ff; font-weight: 500; }}
        .tabs {{ display: flex; gap: 10px; margin-bottom: 20px; }}
        .tab {{ padding: 10px 20px; background: #e0e0e0; cursor: pointer; border-radius: 4px; }}
        .tab.active {{ background: #26a69a; color: white; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        iframe {{ width: 100%; height: 500px; border: none; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{name}</h1>
            <div class="subtitle">Trading Strategy Performance Dashboard</div>
            <div class="meta">
                <div class="meta-item">
                    <span class="meta-label">Timeframe</span>
                    <span class="meta-value">{timeframe}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Date Range</span>
                    <span class="meta-value">{date_range}</span>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Performance Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Total Return</div>
                    <div class="metric-value {self._get_value_class("total_return")}">{results.get("total_return", 0):+.2f}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Sharpe Ratio</div>
                    <div class="metric-value">{results.get("sharpe_ratio", 0):.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Max Drawdown</div>
                    <div class="metric-value negative">{results.get("max_drawdown", 0):.2f}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Trades</div>
                    <div class="metric-value">{results.get("total_trades", 0)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Win Rate</div>
                    <div class="metric-value">{results.get("win_rate", 0):.1f}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Final Capital</div>
                    <div class="metric-value">${results.get("final_capital", 0):,.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Profit Factor</div>
                    <div class="metric-value">{results.get("profit_factor", 0):.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Average Trade</div>
                    <div class="metric-value">${results.get("avg_trade", 0):.2f}</div>
                </div>
            </div>
        </div>
"""

        # Add config section
        if config:
            html += """
        <div class="section">
            <h2>Strategy Configuration</h2>
            <table class="config-table">
                <thead>
                    <tr><th>Parameter</th><th>Value</th></tr>
                </thead>
                <tbody>
"""
            for key, value in config.items():
                row_class = "highlight" if key in ["timeframe", "date_range"] else ""
                html += f'                    <tr class="{row_class}"><td>{key}</td><td>{value}</td></tr>\n'
            html += """
                </tbody>
            </table>
        </div>
"""

        # Generate iframes to plot files
        html += """
        <div class="section">
            <h2>Performance Charts</h2>
            <div class="tabs">
                <div class="tab active" onclick="showTab('equity')">Equity Curve</div>
                <div class="tab" onclick="showTab('drawdown')">Drawdown</div>
 """
        if df is not None:
            html += """
                <div class="tab" onclick="showTab('monthly')">Monthly Returns</div>
                <div class="tab" onclick="showTab('performance')">Trade Timeline</div>
                <div class="tab" onclick="showTab('winrate')">Win Rate</div>
                <div class="tab" onclick="showTab('duration')">Duration Dist</div>
                <div class="tab" onclick="showTab('position')">Position Size</div>
 """
        html += """                <div class="tab" onclick="showTab('pnl')">PnL Distribution</div>
            </div>

            <div id="equity" class="tab-content active">
                <iframe src="equity_curve.html"></iframe>
            </div>
            <div id="drawdown" class="tab-content">
                <iframe src="drawdown.html"></iframe>
            </div>
 """
        if df is not None:
            html += """
            <div id="monthly" class="tab-content">
                <iframe src="monthly_returns.html"></iframe>
            </div>
            <div id="performance" class="tab-content">
                <iframe src="trade_performance_timeline.html"></iframe>
            </div>
            <div id="winrate" class="tab-content">
                <iframe src="win_rate_over_time.html"></iframe>
            </div>
            <div id="duration" class="tab-content">
                 <iframe src="trade_duration_distribution.html"></iframe>
             </div>
             <div id="position" class="tab-content">
                 <iframe src="position_size_over_time.html"></iframe>
             </div>
  """
        html += """            <div id="pnl" class="tab-content">
                 <iframe src="pnl_distribution.html"></iframe>
             </div>
         </div>
  """

        # Add script tag for tabs
        html += """
    </div>

    <script>
        function showTab(tabId) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected tab
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
"""

        return html

    def generate_summary(self) -> str:
        """Generate text summary

        Returns:
            Summary string
        """
        summary = f"""
{self.name}
{"=" * 80}

Performance Metrics:
  Total Return:       {self.results.get("total_return", 0):+.2f}%
  Sharpe Ratio:        {self.results.get("sharpe_ratio", 0):.2f}
  Max Drawdown:       {self.results.get("max_drawdown", 0):.2f}%
  Total Trades:         {self.results.get("total_trades", 0)}
  Win Rate:           {self.results.get("win_rate", 0):.1f}%
  Final Capital:       ${self.results.get("final_capital", 0):,.2f}
  Profit Factor:       {self.results.get("profit_factor", 0):.2f}
  Average Trade:      ${self.results.get("avg_trade", 0):.2f}
"""
        if self.buy_hold:
            summary += f"""
Buy & Hold Comparison:
  Strategy Return:    {self.results.get("total_return", 0):+.2f}%
  Buy & Hold Return:  {self.buy_hold.get("total_return_pct", 0):+.2f}%
  Difference:          {self.results.get("total_return", 0) - self.buy_hold.get("total_return_pct", 0):+.2f}%
"""
        return summary
