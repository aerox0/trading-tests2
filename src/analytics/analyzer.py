"""Results analysis and insights generation"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from .metrics import (
    calculate_calmar_ratio,
    calculate_sortino_ratio,
    calculate_win_streak,
    calculate_loss_streak,
    calculate_monthly_returns,
    calculate_profit_distribution,
    calculate_annualized_metrics,
    calculate_drawdown_series,
)


class ResultsAnalyzer:
    """Analyze backtest results and generate insights"""

    def __init__(
        self,
        results: Dict[str, Any],
        df: Optional[pd.DataFrame] = None,
        name: Optional[str] = "Strategy",
    ):
        """Initialize analyzer

        Args:
            results: Backtest results dictionary
            df: OHLCV DataFrame (optional)
            name: Strategy name
        """
        self.results = results
        self.df = df
        self.name = name
        self.equity_curve = results.get("equity_curve", [])
        self.trades = results.get("trades", [])
        self.timestamps = df.index if df is not None else None

    def analyze(self) -> Dict[str, Any]:
        """Perform comprehensive analysis

        Returns:
            Dictionary with all analysis results
        """
        analysis = {}

        # Basic metrics from results
        analysis["basic"] = self.results.copy()

        # Advanced risk metrics
        analysis["risk"] = self._calculate_risk_metrics()

        # Trading statistics
        analysis["trading"] = self._calculate_trading_stats()

        # Monthly performance
        if self.timestamps is not None:
            analysis["monthly"] = self._calculate_monthly_stats()

        # Profit distribution
        analysis["profit_dist"] = self._calculate_profit_distribution()

        # Insights
        analysis["insights"] = self._generate_insights()

        return analysis

    def get_trades_df(self) -> pd.DataFrame:
        """Get trades as DataFrame

        Returns:
            DataFrame with trade details
        """
        if not self.trades:
            return pd.DataFrame()

        trades_df = pd.DataFrame(self.trades)

        if self.timestamps is not None and "equity_curve" in self.results:
            # Add timestamps based on equity curve points
            equity_len = len(self.equity_curve)
            if len(trades_df) <= equity_len:
                # Simple mapping - in real scenario, would track trade indices
                pass

        return trades_df

    def get_monthly_returns(self) -> pd.DataFrame:
        """Get monthly returns

        Returns:
            DataFrame with monthly returns
        """
        if self.timestamps is None:
            return pd.DataFrame()

        return calculate_monthly_returns(self.equity_curve, self.timestamps)

    def get_drawdown_series(self) -> pd.Series:
        """Get drawdown series

        Returns:
            Series with drawdown percentages
        """
        return calculate_drawdown_series(self.equity_curve)

    def _calculate_risk_metrics(self) -> Dict[str, float]:
        """Calculate risk-adjusted metrics

        Returns:
            Dictionary with risk metrics
        """
        if not self.equity_curve:
            return {}

        returns = np.diff(self.equity_curve) / np.array(self.equity_curve[:-1])

        metrics = {}

        # Calmar ratio
        total_return = self.results.get("total_return", 0)
        max_dd = self.results.get("max_drawdown", 0)
        metrics["calmar_ratio"] = calculate_calmar_ratio(total_return, max_dd)

        # Sortino ratio
        metrics["sortino_ratio"] = calculate_sortino_ratio(returns)

        # Annualized metrics
        if self.timestamps is not None:
            annualized = calculate_annualized_metrics(
                self.equity_curve, self.timestamps
            )
            metrics["annualized_return"] = annualized["annualized_return"]
            metrics["annualized_volatility"] = annualized["annualized_volatility"]

        # Drawdown statistics
        dd_series = self.get_drawdown_series()
        if len(dd_series) > 0:
            metrics["avg_drawdown"] = dd_series[dd_series < 0].mean()
            metrics["drawdown_duration_avg"] = 0  # Placeholder
            metrics["drawdown_duration_max"] = 0  # Placeholder

        return metrics

    def _calculate_trading_stats(self) -> Dict[str, float]:
        """Calculate trading statistics

        Returns:
            Dictionary with trading statistics
        """
        if not self.trades:
            return {
                "win_streak_max": 0,
                "loss_streak_max": 0,
            }

        pnls = [t["pnl"] for t in self.trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]

        stats = {}

        # Streaks
        stats["win_streak_max"] = calculate_win_streak(self.trades)
        stats["loss_streak_max"] = calculate_loss_streak(self.trades)

        # Profit distribution
        profit_dist = calculate_profit_distribution(self.trades)
        stats["largest_win"] = profit_dist["largest_win"]
        stats["largest_loss"] = profit_dist["largest_loss"]
        stats["profit_factor"] = profit_dist["profit_factor"]
        stats["expected_value_per_trade"] = profit_dist["expected_value"]

        # Win/Loss amounts
        stats["avg_win"] = profit_dist["avg_win"]
        stats["avg_loss"] = profit_dist["avg_loss"]

        return stats

    def _calculate_monthly_stats(self) -> Dict[str, float]:
        """Calculate monthly performance statistics

        Returns:
            Dictionary with monthly statistics
        """
        monthly_df = self.get_monthly_returns()

        if monthly_df.empty:
            return {}

        stats = {}

        returns = monthly_df["return_pct"].values
        stats["best_month_return"] = returns.max()
        stats["worst_month_return"] = returns.min()
        stats["avg_monthly_return"] = returns.mean()
        stats["monthly_std"] = returns.std()

        # Count positive vs negative months
        stats["positive_months"] = (returns > 0).sum()
        stats["negative_months"] = (returns < 0).sum()
        stats["total_months"] = len(returns)

        return stats

    def _calculate_profit_distribution(self) -> Dict[str, float]:
        """Calculate profit distribution statistics

        Returns:
            Dictionary with profit distribution
        """
        if not self.trades:
            return {}

        pnls = [t["pnl"] for t in self.trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]

        dist = {}

        # Win/Loss ratio
        if losses:
            dist["win_loss_ratio"] = sum(wins) / abs(sum(losses))
        else:
            dist["win_loss_ratio"] = np.inf if wins else 0

        # Median trade
        dist["median_trade_pnl"] = np.median(pnls)
        dist["median_win"] = np.median(wins) if wins else 0
        dist["median_loss"] = np.median(losses) if losses else 0

        return dist

    def _generate_insights(self) -> List[str]:
        """Generate insights about strategy performance

        Returns:
            List of insight strings
        """
        insights = []

        if not self.trades:
            insights.append("No trades executed")
            return insights

        total_return = self.results.get("total_return", 0)
        sharpe = self.results.get("sharpe_ratio", 0)
        max_dd = self.results.get("max_drawdown", 0)
        win_rate = self.results.get("win_rate", 0)
        profit_factor = self._calculate_trading_stats().get("profit_factor", 0)

        # Overall performance
        if total_return > 0:
            insights.append(f"Strategy is profitable with {total_return:+.2f}% return")
        else:
            insights.append(
                f"Strategy is unprofitable with {total_return:+.2f}% return"
            )

        # Risk-adjusted performance
        if sharpe > 1.5:
            insights.append("Excellent risk-adjusted returns (Sharpe > 1.5)")
        elif sharpe > 1.0:
            insights.append("Good risk-adjusted returns (Sharpe > 1.0)")
        elif sharpe > 0.5:
            insights.append("Moderate risk-adjusted returns (Sharpe > 0.5)")
        else:
            insights.append("Poor risk-adjusted returns (Sharpe < 0.5)")

        # Drawdown
        if abs(max_dd) < 10:
            insights.append("Low drawdown (under 10%) - excellent risk control")
        elif abs(max_dd) < 20:
            insights.append("Moderate drawdown (10-20%) - acceptable risk")
        elif abs(max_dd) < 30:
            insights.append("High drawdown (20-30%) - consider position sizing")
        else:
            insights.append("Very high drawdown (over 30%) - review risk management")

        # Win rate vs profit factor
        if win_rate < 40 and profit_factor > 1.5:
            insights.append(
                "Low win rate but high profit factor - few big winners compensate for many losses"
            )
        elif win_rate > 50 and profit_factor < 1.2:
            insights.append(
                "High win rate but low profit factor - small winners may not cover big losers"
            )
        elif win_rate < 35:
            insights.append(
                "Low win rate (<35%) - requires large winners or tight stops"
            )

        # Trading frequency
        total_trades = len(self.trades)
        if total_trades < 50:
            insights.append(
                f"Low trade count ({total_trades}) - may not have enough statistical significance"
            )
        elif total_trades > 500:
            insights.append(
                f"High trade count ({total_trades}) - consider transaction costs"
            )

        return insights

    def get_summary_dict(self) -> Dict[str, Any]:
        """Get summary dictionary for reporting

        Returns:
            Dictionary with key metrics and insights
        """
        analysis = self.analyze()

        summary = {
            "strategy_name": self.name,
            "period": self._get_period_range(),
            "metrics": {
                "Performance": {
                    "Total Return": f"{analysis['basic']['total_return']:+.2f}%",
                    "Sharpe Ratio": f"{analysis['basic']['sharpe_ratio']:.2f}",
                    "Max Drawdown": f"{analysis['basic']['max_drawdown']:.2f}%",
                },
                "Risk-Adjusted": {
                    "Calmar Ratio": f"{analysis['risk'].get('calmar_ratio', 0):.2f}",
                    "Sortino Ratio": f"{analysis['risk'].get('sortino_ratio', 0):.2f}",
                    "Annualized Return": f"{analysis['risk'].get('annualized_return', 0):.2f}%",
                    "Annualized Volatility": f"{analysis['risk'].get('annualized_volatility', 0):.2f}%",
                },
                "Trading": {
                    "Total Trades": analysis["basic"]["total_trades"],
                    "Win Rate": f"{analysis['basic']['win_rate']:.1f}%",
                    "Profit Factor": f"{analysis['trading'].get('profit_factor', 0):.2f}",
                    "Avg Trade": f"${analysis['basic']['avg_trade']:.2f}",
                },
                "Win/Loss": {
                    "Avg Win": f"${analysis['trading'].get('avg_win', 0):.2f}",
                    "Avg Loss": f"-${abs(analysis['trading'].get('avg_loss', 0)):.2f}",
                    "Largest Win": f"${analysis['trading'].get('largest_win', 0):.2f}",
                    "Largest Loss": f"-${abs(analysis['trading'].get('largest_loss', 0)):.2f}",
                    "Max Win Streak": analysis["trading"]["win_streak_max"],
                    "Max Loss Streak": analysis["trading"]["loss_streak_max"],
                },
            },
            "insights": analysis["insights"],
        }

        return summary

    def _get_period_range(self) -> str:
        """Get date range string

        Returns:
            Date range string
        """
        if self.timestamps is None:
            return "Unknown"

        start = self.timestamps[0]
        end = self.timestamps[-1]

        return f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"

    def print_summary(self):
        """Print formatted summary to console"""
        summary = self.get_summary_dict()

        print("\n" + "=" * 80)
        print(f"                    {summary['strategy_name'].upper()}")
        print("=" * 80)
        print(f"Period: {summary['period']}")
        print()

        for category, metrics in summary["metrics"].items():
            print(f"{category}:")
            print("-" * 40)
            for key, value in metrics.items():
                print(f"  {key:20s}: {value}")
            print()

        print("Key Insights:")
        print("-" * 40)
        for insight in summary["insights"]:
            print(f"  • {insight}")

        print("=" * 80)
