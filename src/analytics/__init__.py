"""Analytics and reporting module for trading strategies"""

from typing import Dict, Any, Optional, List
import pandas as pd
from pathlib import Path
from datetime import datetime

from .analyzer import ResultsAnalyzer
from .reports import ReportGenerator
from .comparator import StrategyComparator
from .metrics import *
from .plots import *
from .utils import *


class Analytics:
    """High-level analytics API for trading strategies

    Simple, unified interface for:
    - Analyzing results
    - Generating plots
    - Creating reports (CSV, HTML, JSON)
    - Comparing strategies
    - Console output
    """

    def __init__(
        self,
        results: Dict[str, Any],
        df: Optional[pd.DataFrame] = None,
        name: str = "Strategy",
        config: Optional[Dict] = None,
        buy_hold_results: Optional[Dict] = None,
        output_dir: Optional[str] = None,
    ):
        """Initialize analytics

        Args:
            results: Backtest results dictionary
            df: OHLCV DataFrame (optional)
            name: Strategy name
            config: Strategy configuration (optional)
            buy_hold_results: Buy & Hold baseline (optional)
            output_dir: Output directory (defaults to outputs/timestamp/strategy_name)
        """
        self.results = results
        self.df = df
        self.name = name
        self.config = config or {}
        self.buy_hold_results = buy_hold_results

        # Create timestamped output directory
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = name.replace(" ", "_").replace("/", "_").lower()
            self.output_dir = Path("outputs") / timestamp / safe_name
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize analyzer
        self.analyzer = ResultsAnalyzer(results, df=df, name=name)

        # Initialize report generator
        self.report_gen = ReportGenerator(
            results,
            strategy_name=name,
            config=config,
            buy_hold_results=buy_hold_results,
        )

    def print_summary(self):
        """Print formatted summary to console"""
        self.analyzer.print_summary()

    def analyze(self) -> Dict[str, Any]:
        """Perform comprehensive analysis

        Returns:
            Analysis dictionary with all metrics and insights
        """
        return self.analyzer.analyze()

    def get_trades_df(self) -> pd.DataFrame:
        """Get trades as DataFrame

        Returns:
            DataFrame with trade details
        """
        return self.analyzer.get_trades_df()

    def get_monthly_returns(self) -> pd.DataFrame:
        """Get monthly returns

        Returns:
            DataFrame with monthly returns
        """
        return self.analyzer.get_monthly_returns()

    def get_drawdown_series(self) -> pd.Series:
        """Get drawdown series

        Returns:
            Series with drawdown percentages
        """
        return self.analyzer.get_drawdown_series()

    def plot_all(self, output_dir: Optional[str] = None):
        """Generate all standard plots

        Args:
            output_dir: Directory to save plots (defaults to self.output_dir)
        """
        output_path = Path(output_dir) if output_dir else self.output_dir
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\nGenerating plots in {output_path}...")

        self.plot_equity_curve(save_path=str(output_path / "equity_curve.html"))
        self.plot_drawdown(save_path=str(output_path / "drawdown.html"))

        if self.df is not None:
            self.plot_monthly_returns(
                save_path=str(output_path / "monthly_returns.html")
            )
            self.plot_trade_performance_timeline(
                save_path=str(output_path / "trade_performance_timeline.html")
            )
            self.plot_win_rate_over_time(
                save_path=str(output_path / "win_rate_over_time.html")
            )
            self.plot_trade_duration_distribution(
                save_path=str(output_path / "trade_duration_distribution.html")
            )
            self.plot_position_size_over_time(
                save_path=str(output_path / "position_size_over_time.html")
            )

        self.plot_pnl_distribution(save_path=str(output_path / "pnl_distribution.html"))

        print(f"\nAll plots saved to {output_path.absolute()}")

    def plot_equity_curve(
        self, save_path: Optional[str] = None, include_buy_hold: bool = False
    ):
        """Plot equity curve

        Args:
            save_path: Path to save plot (defaults to output_dir/equity_curve.html)
            include_buy_hold: Whether to include Buy & Hold benchmark (default: False)

        Returns:
            Plotly figure object
        """
        if save_path is None:
            save_path = str(self.output_dir / "equity_curve.html")
        return plot_equity_curve(
            self.results,
            df=self.df,
            name=self.name,
            buy_hold_results=self.buy_hold_results,
            save_path=save_path,
            include_buy_hold=include_buy_hold,
        )

    def plot_drawdown(
        self,
        save_path: Optional[str] = None,
        include_buy_hold: bool = False,
    ):
        """Plot drawdown chart

        Args:
            save_path: Path to save plot (defaults to output_dir/drawdown.html)
            include_buy_hold: Whether to include Buy & Hold benchmark (default: False)

        Returns:
            Plotly figure object
        """
        if save_path is None:
            save_path = str(self.output_dir / "drawdown.html")
        return plot_drawdown(
            self.results,
            df=self.df,
            name=self.name,
            save_path=save_path,
            buy_hold_results=self.buy_hold_results,
            include_buy_hold=include_buy_hold,
        )

    def plot_monthly_returns(
        self,
        save_path: Optional[str] = None,
        use_bar_chart: bool = True,
        include_buy_hold: bool = False,
    ):
        """Plot monthly returns

        Args:
            save_path: Path to save plot (defaults to output_dir/monthly_returns.html)
            use_bar_chart: If True, use bar chart; if False, use heatmap
            include_buy_hold: Whether to include Buy & Hold benchmark (default: False)

        Returns:
            Plotly figure object
        """
        if self.df is None:
            print("No dataframe available for monthly returns")
            return None

        if save_path is None:
            save_path = str(self.output_dir / "monthly_returns.html")
        return plot_monthly_returns(
            self.results,
            timestamps=self.df.index,
            df=self.df,
            name=self.name,
            use_bar_chart=use_bar_chart,
            save_path=save_path,
            buy_hold_results=self.buy_hold_results,
            include_buy_hold=include_buy_hold,
        )

    def plot_pnl_distribution(self, save_path: Optional[str] = None):
        """Plot PnL distribution

        Args:
            save_path: Path to save plot (defaults to output_dir/pnl_distribution.html)

        Returns:
            Plotly figure object
        """
        if save_path is None:
            save_path = str(self.output_dir / "pnl_distribution.html")
        return plot_pnl_distribution(self.results, name=self.name, save_path=save_path)

    def plot_trade_performance_timeline(self, save_path: Optional[str] = None):
        """Plot trade performance timeline (Chart C)

        Args:
            save_path: Path to save plot (defaults to output_dir/trade_performance_timeline.html)

        Returns:
            Plotly figure object
        """
        if save_path is None:
            save_path = str(self.output_dir / "trade_performance_timeline.html")
        return plot_trade_performance_timeline(
            self.results, name=self.name, save_path=save_path
        )

    def plot_win_rate_over_time(
        self, save_path: Optional[str] = None, window: int = 20
    ):
        """Plot win rate over time (Chart D)

        Args:
            save_path: Path to save plot (defaults to output_dir/win_rate_over_time.html)
            window: Rolling window size for win rate calculation

        Returns:
            Plotly figure object
        """
        if save_path is None:
            save_path = str(self.output_dir / "win_rate_over_time.html")
        return plot_win_rate_over_time(
            self.results, name=self.name, window=window, save_path=save_path
        )

    def plot_trade_duration_distribution(self, save_path: Optional[str] = None):
        """Plot trade duration distribution

        Args:
            save_path: Path to save plot (defaults to output_dir/trade_duration_distribution.html)

        Returns:
            Plotly figure object
        """
        if save_path is None:
            save_path = str(self.output_dir / "trade_duration_distribution.html")
        return plot_trade_duration_distribution(
            self.results, name=self.name, save_path=save_path
        )

    def plot_position_size_over_time(self, save_path: Optional[str] = None):
        """Plot position size over time

        Args:
            save_path: Path to save plot (defaults to output_dir/position_size_over_time.html)

        Returns:
            Plotly figure object
        """
        if save_path is None:
            save_path = str(self.output_dir / "position_size_over_time.html")
        return plot_position_size_over_time(
            self.results, name=self.name, save_path=save_path
        )

    def save_csv(
        self,
        path: Optional[str] = None,
        include_trades: bool = True,
        include_equity: bool = False,
    ):
        """Export results to CSV

        Args:
            path: Output CSV path (defaults to output_dir/metrics.csv)
            include_trades: Include trade log
            include_equity: Include equity curve
        """
        if path is None:
            path = str(self.output_dir / "metrics.csv")
        self.report_gen.to_csv(
            path, include_trades=include_trades, include_equity=include_equity
        )

    def save_json(self, path: Optional[str] = None):
        """Export results to JSON

        Args:
            path: Output JSON path (defaults to output_dir/report.json)
        """
        if path is None:
            path = str(self.output_dir / "report.json")
        self.report_gen.to_json(path)

    def save_html(self, path: Optional[str] = None):
        """Export results to HTML

        Args:
            path: Output HTML path (defaults to output_dir/report.html)
        """
        if path is None:
            path = str(self.output_dir / "report.html")
        self.report_gen.to_html(path)

    def generate_summary(self) -> str:
        """Generate text summary

        Returns:
            Summary string
        """
        return self.report_gen.generate_summary()

    def get_summary_dict(self) -> Dict[str, Any]:
        """Get summary dictionary

        Returns:
            Dictionary with key metrics and insights
        """
        return self.analyzer.get_summary_dict()

    def generate_dashboard(
        self, filename: str = "dashboard.html", include_buy_hold: bool = False
    ):
        """Generate single HTML dashboard with all plots and metrics

        Args:
            filename: Output HTML filename
            include_buy_hold: Whether to include Buy & Hold in charts (default: False)
        """
        # Generate individual plots first
        self.plot_equity_curve(include_buy_hold=include_buy_hold)
        self.plot_drawdown(include_buy_hold=include_buy_hold)
        if self.df is not None:
            self.plot_monthly_returns(include_buy_hold=include_buy_hold)
            self.plot_trade_performance_timeline()
            self.plot_win_rate_over_time()
            self.plot_trade_duration_distribution()
            self.plot_position_size_over_time()
        self.plot_pnl_distribution()

        # Generate dashboard HTML with iframes
        html = self.report_gen._generate_html_report_with_charts(
            self.results,
            self.df,
            self.name,
            self.config,
            include_buy_hold=include_buy_hold,
        )

        output_path = self.output_dir / filename
        with open(output_path, "w") as f:
            f.write(html)

        print(f"Saved dashboard to {output_path}")

        return output_path


def compare_strategies(
    results_dict: Dict[str, Dict[str, Any]],
    metrics: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Compare multiple strategies

    Args:
        results_dict: Dictionary of {name: results}
        metrics: List of metrics to compare

    Returns:
        Comparison DataFrame
    """
    comparator = StrategyComparator()

    for name, results in results_dict.items():
        comparator.add_result(name, results)

    return comparator.compare(metrics=metrics)


def rank_strategies(
    results_dict: Dict[str, Dict[str, Any]], by: str = "sharpe_ratio"
) -> pd.DataFrame:
    """Rank strategies by metric

    Args:
        results_dict: Dictionary of {name: results}
        by: Metric to rank by

    Returns:
        Ranked DataFrame
    """
    comparator = StrategyComparator()

    for name, results in results_dict.items():
        comparator.add_result(name, results)

    return comparator.rank(by=by)


def plot_strategy_comparison(
    results_dict: Dict[str, Dict[str, Any]], save_path: Optional[str] = None
):
    """Plot strategy comparison

    Args:
        results_dict: Dictionary of {name: results}
        save_path: Path to save plot

    Returns:
        Plotly figure object
    """
    from .plots import plot_equity_comparison

    return plot_equity_comparison(results_dict, save_path=save_path)


def plot_metrics_comparison(
    results_dict: Dict[str, Dict[str, Any]],
    metrics: List[str],
    save_path: Optional[str] = None,
):
    """Plot metrics comparison

    Args:
        results_dict: Dictionary of {name: results}
        metrics: List of metrics to compare
        save_path: Path to save plot

    Returns:
        Plotly figure object
    """
    from .plots import plot_metrics_comparison

    return plot_metrics_comparison(results_dict, metrics, save_path=save_path)


def generate_comparison_reports(
    results_dict: Dict[str, Dict[str, Any]], output_dir: str = "comparison_reports"
):
    """Generate comparison reports for all strategies

    Args:
        results_dict: Dictionary of {name: results}
        output_dir: Output directory for reports
    """
    comparator = StrategyComparator()

    for name, results in results_dict.items():
        comparator.add_result(name, results)

    comparator.save_comparison_report(output_dir=output_dir)


__all__ = [
    # Main API
    "Analytics",
    # Convenience functions
    "compare_strategies",
    "rank_strategies",
    "plot_strategy_comparison",
    "plot_metrics_comparison",
    "generate_comparison_reports",
    # Submodules
    "ResultsAnalyzer",
    "ReportGenerator",
    "StrategyComparator",
]
