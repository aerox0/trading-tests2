"""Multi-strategy comparison and ranking"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from .reports import ReportGenerator
from .plots import (
    plot_equity_comparison,
    plot_radar_chart,
    plot_metrics_comparison,
)


class StrategyComparator:
    """Compare multiple strategies or parameter variations"""

    def __init__(self):
        """Initialize comparator"""
        self.results_dict: Dict[str, Dict[str, Any]] = {}
        self.dataframes: Dict[str, pd.DataFrame] = {}

    def add_result(
        self,
        name: str,
        results: Dict[str, Any],
        df: Optional[pd.DataFrame] = None,
        config: Optional[Dict] = None,
    ):
        """Add strategy results for comparison

        Args:
            name: Strategy/parameter set name
            results: Backtest results dictionary
            df: OHLCV DataFrame (optional)
            config: Strategy configuration (optional)
        """
        self.results_dict[name] = {
            "results": results,
            "df": df,
            "config": config or {},
        }

    def compare(
        self,
        metrics: Optional[List[str]] = None,
        format: str = "table",
    ) -> pd.DataFrame:
        """Compare strategies on specified metrics

        Args:
            metrics: List of metrics to compare (default: all key metrics)
            format: Output format ('table', 'csv')

        Returns:
            Comparison DataFrame
        """
        if not self.results_dict:
            print("No results to compare")
            return pd.DataFrame()

        if metrics is None:
            metrics = [
                "total_return",
                "sharpe_ratio",
                "max_drawdown",
                "total_trades",
                "win_rate",
                "profit_factor",
                "avg_trade",
            ]

        # Build comparison DataFrame
        comparison_data = {}

        for name, data in self.results_dict.items():
            results = data["results"]
            row = {}

            for metric in metrics:
                value = results.get(metric, 0)
                row[metric] = value

            comparison_data[name] = row

        df = pd.DataFrame.from_dict(comparison_data, orient="index")
        df = df[metrics]

        if format == "table":
            print("\n" + "=" * 80)
            print("STRATEGY COMPARISON")
            print("=" * 80)
            print(df.to_string())
            print("=" * 80)

        return df

    def rank(self, by: str = "sharpe_ratio", ascending: bool = False) -> pd.DataFrame:
        """Rank strategies by specified metric

        Args:
            by: Metric to rank by (default: sharpe_ratio)
            ascending: Sort order (default: False for descending)

        Returns:
            Ranked DataFrame
        """
        comparison_df = self.compare(metrics=[by], format="table")

        if comparison_df.empty:
            return pd.DataFrame()

        ranked = comparison_df.sort_values(by=by, ascending=ascending)

        print("\n" + "=" * 80)
        print(f"STRATEGY RANKING (by: {by})")
        print("=" * 80)
        print(ranked.to_string())
        print("=" * 80)

        return ranked

    def plot_comparison(self, save_path: Optional[str] = None):
        """Plot equity curve comparison

        Args:
            save_path: Path to save plot (optional)
        """
        # Prepare results dict for plotting
        results_for_plot = {
            name: data["results"] for name, data in self.results_dict.items()
        }

        fig = plot_equity_comparison(results_for_plot, save_path=save_path)

        return fig

    def plot_radar_chart(
        self,
        metrics: List[str],
        save_path: Optional[str] = None,
    ):
        """Plot radar chart for multi-metric comparison

        Args:
            metrics: List of metrics to compare
            save_path: Path to save plot (optional)
        """
        # Prepare results dict for plotting
        results_for_plot = {
            name: data["results"] for name, data in self.results_dict.items()
        }

        fig = plot_radar_chart(results_for_plot, metrics, save_path=save_path)

        return fig

    def plot_metrics_comparison(
        self,
        metrics: List[str],
        save_path: Optional[str] = None,
    ):
        """Plot bar chart for metrics comparison

        Args:
            metrics: List of metrics to compare
            save_path: Path to save plot (optional)
        """
        # Prepare results dict for plotting
        results_for_plot = {
            name: data["results"] for name, data in self.results_dict.items()
        }

        fig = plot_metrics_comparison(results_for_plot, metrics, save_path=save_path)

        return fig

    def print_comparison(
        self,
        metrics: Optional[List[str]] = None,
    ):
        """Print detailed comparison

        Args:
            metrics: List of metrics to compare
        """
        if metrics is None:
            metrics = [
                "total_return",
                "sharpe_ratio",
                "max_drawdown",
                "total_trades",
                "win_rate",
                "profit_factor",
            ]

        print("\n" + "=" * 80)
        print("DETAILED STRATEGY COMPARISON")
        print("=" * 80)

        for name, data in self.results_dict.items():
            results = data["results"]
            config = data["config"]

            print(f"\n{name}:")
            print("-" * 40)

            for metric in metrics:
                value = results.get(metric, 0)
                print(f"  {metric:20s}: {value}")

            if config:
                print(f"\n  Configuration:")
                for key, value in list(config.items())[:5]:  # Show first 5 params
                    print(f"    {key}: {value}")
                if len(config) > 5:
                    print(f"    ... and {len(config) - 5} more")

        print("\n" + "=" * 80)

    def save_comparison_csv(self, path: str):
        """Save comparison to CSV

        Args:
            path: Output CSV path
        """
        comparison_df = self.compare(format="csv")
        comparison_df.to_csv(path)

        print(f"Saved comparison CSV to {path}")

    def save_comparison_report(
        self,
        output_dir: str = "comparison_reports",
    ):
        """Generate comparison reports for all strategies

        Args:
            output_dir: Output directory for reports
        """
        from pathlib import Path
        import os

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print("\n" + "=" * 80)
        print("GENERATING COMPARISON REPORTS")
        print("=" * 80)

        # Generate individual reports
        for name, data in self.results_dict.items():
            results = data["results"]
            config = data["config"]
            df = data["df"]

            # Create report generator
            report_gen = ReportGenerator(results, strategy_name=name, config=config)

            # Save reports
            csv_path = output_path / f"{name}_metrics.csv"
            report_gen.to_csv(str(csv_path))

            json_path = output_path / f"{name}_report.json"
            report_gen.to_json(str(json_path))

            print(f"Generated reports for {name}")

        # Generate comparison CSV
        comparison_path = output_path / "comparison.csv"
        self.save_comparison_csv(str(comparison_path))

        # Generate comparison plots
        print("\nGenerating comparison plots...")

        equity_plot_path = output_path / "equity_comparison.html"
        self.plot_comparison(save_path=str(equity_plot_path))

        # Generate metrics comparison plot
        key_metrics = [
            "total_return",
            "sharpe_ratio",
            "max_drawdown",
            "win_rate",
        ]
        metrics_plot_path = output_path / "metrics_comparison.html"
        self.plot_metrics_comparison(key_metrics, save_path=str(metrics_plot_path))

        # Generate radar chart
        radar_plot_path = output_path / "radar_comparison.html"
        self.plot_radar_chart(key_metrics, save_path=str(radar_plot_path))

        print("\n" + "=" * 80)
        print(f"All reports generated in: {output_path.absolute()}")
        print("=" * 80)

    def get_best_strategy(
        self,
        by: str = "sharpe_ratio",
    ) -> tuple:
        """Get best strategy by specified metric

        Args:
            by: Metric to use for selection

        Returns:
            Tuple of (name, results)
        """
        if not self.results_dict:
            return None, None

        best_name = None
        best_value = float("-inf")

        for name, data in self.results_dict.items():
            value = data["results"].get(by, 0)

            if value > best_value:
                best_value = value
                best_name = name

        print(f"\nBest strategy by {by}: {best_name} ({best_value:.2f})")

        return best_name, self.results_dict[best_name]

    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get summary statistics across all strategies

        Returns:
            Dictionary with summary statistics
        """
        if not self.results_dict:
            return {}

        summary = {
            "num_strategies": len(self.results_dict),
            "strategy_names": list(self.results_dict.keys()),
        }

        # Calculate statistics for key metrics
        key_metrics = [
            "total_return",
            "sharpe_ratio",
            "max_drawdown",
            "profit_factor",
        ]

        for metric in key_metrics:
            values = [
                data["results"].get(metric, 0) for data in self.results_dict.values()
            ]

            summary[f"{metric}_mean"] = np.mean(values)
            summary[f"{metric}_std"] = np.std(values)
            summary[f"{metric}_min"] = np.min(values)
            summary[f"{metric}_max"] = np.max(values)

        return summary

    def print_statistics_summary(self):
        """Print summary statistics"""
        summary = self.get_statistics_summary()

        print("\n" + "=" * 80)
        print("COMPARISON STATISTICS")
        print("=" * 80)
        print(f"Number of Strategies: {summary['num_strategies']}")
        print(f"Strategy Names: {', '.join(summary['strategy_names'])}")

        print("\nMetric Statistics:")

        for metric in [
            "total_return",
            "sharpe_ratio",
            "max_drawdown",
            "profit_factor",
        ]:
            print(f"\n{metric}:")
            print(f"  Mean: {summary[f'{metric}_mean']:.2f}")
            print(f"  Std:  {summary[f'{metric}_std']:.2f}")
            print(f"  Min:  {summary[f'{metric}_min']:.2f}")
            print(f"  Max:  {summary[f'{metric}_max']:.2f}")

        print("=" * 80)
