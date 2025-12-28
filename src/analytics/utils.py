"""Helper functions for analytics"""

import pandas as pd
from typing import Any, List


def format_currency(value: float, decimals: int = 2) -> str:
    """Format value as currency

    Args:
        value: Numeric value
        decimals: Number of decimal places

    Returns:
        Formatted currency string
    """
    return f"${value:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format value as percentage

    Args:
        value: Numeric value
        decimals: Number of decimal places

    Returns:
        Formatted percentage string
    """
    return f"{value:+.{decimals}f}%"


def format_number(value: float, decimals: int = 2) -> str:
    """Format value with comma separators

    Args:
        value: Numeric value
        decimals: Number of decimal places

    Returns:
        Formatted number string
    """
    return f"{value:,.{decimals}f}"


def get_period_range(timestamps: pd.DatetimeIndex) -> str:
    """Get date range string from timestamps

    Args:
        timestamps: Pandas DatetimeIndex

    Returns:
        Date range string
    """
    if timestamps is None or len(timestamps) == 0:
        return "Unknown"

    start = timestamps[0]
    end = timestamps[-1]

    return f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"


def get_period_duration(timestamps: pd.DatetimeIndex) -> str:
    """Get human-readable duration string

    Args:
        timestamps: Pandas DatetimeIndex

    Returns:
        Duration string
    """
    if timestamps is None or len(timestamps) == 0:
        return "Unknown"

    duration = timestamps[-1] - timestamps[0]
    days = duration.days

    if days < 30:
        return f"{days} days"
    elif days < 365:
        months = days / 30.44
        return f"{months:.1f} months"
    else:
        years = days / 365.25
        return f"{years:.1f} years"


def get_color_palette(n_colors: int) -> List[str]:
    """Get color palette for plots

    Args:
        n_colors: Number of colors needed

    Returns:
        List of hex color codes
    """
    # Use Plotly's qualitative colors
    plotly_colors = [
        "#1f77b4",  # Blue
        "#ff7f0e",  # Orange
        "#2ca02c",  # Green
        "#d62728",  # Red
        "#9467bd",  # Purple
        "#8c564b",  # Brown
        "#e377c2",  # Pink
        "#7f7f7f",  # Gray
        "#bcbd22",  # Olive
        "#17becf",  # Cyan
    ]

    # Cycle through colors if needed
    palette = []
    for i in range(n_colors):
        palette.append(plotly_colors[i % len(plotly_colors)])

    return palette


def truncate_list(items: List[Any], max_items: int = 5, suffix: str = "...") -> str:
    """Truncate list for display

    Args:
        items: List of items
        max_items: Maximum items to show
        suffix: Suffix to add if truncated

    Returns:
        String representation
    """
    if len(items) <= max_items:
        return ", ".join(str(item) for item in items)

    shown = items[:max_items]
    remaining = len(items) - max_items

    return f"{', '.join(str(item) for item in shown)} {suffix} ({remaining} more)"


def calculate_grade(
    value: float,
    benchmarks: List[tuple],
) -> str:
    """Calculate grade based on value vs benchmarks

    Args:
        value: Value to grade
        benchmarks: List of (threshold, grade) tuples

    Returns:
        Grade string
    """
    for threshold, grade in benchmarks:
        if value >= threshold:
            return grade

    return benchmarks[-1][1] if benchmarks else "N/A"


def get_performance_rating(sharpe: float) -> str:
    """Get performance rating based on Sharpe ratio

    Args:
        sharpe: Sharpe ratio value

    Returns:
        Rating string
    """
    if sharpe >= 2.0:
        return "Excellent"
    elif sharpe >= 1.5:
        return "Very Good"
    elif sharpe >= 1.0:
        return "Good"
    elif sharpe >= 0.5:
        return "Moderate"
    else:
        return "Poor"


def get_drawdown_rating(max_dd: float) -> str:
    """Get drawdown rating

    Args:
        max_dd: Maximum drawdown (negative value)

    Returns:
        Rating string
    """
    abs_dd = abs(max_dd)

    if abs_dd < 10:
        return "Excellent"
    elif abs_dd < 20:
        return "Good"
    elif abs_dd < 30:
        return "Moderate"
    else:
        return "Poor"


def get_win_rate_rating(win_rate: float) -> str:
    """Get win rate rating

    Args:
        win_rate: Win rate percentage (0-100)

    Returns:
        Rating string
    """
    if win_rate >= 50:
        return "Excellent"
    elif win_rate >= 45:
        return "Very Good"
    elif win_rate >= 40:
        return "Good"
    elif win_rate >= 35:
        return "Moderate"
    else:
        return "Poor"


def format_trade_list(trades: List[dict], limit: int = 10) -> str:
    """Format trades list for display

    Args:
        trades: List of trade dictionaries
        limit: Maximum trades to show

    Returns:
        Formatted string
    """
    if not trades:
        return "No trades"

    header = f"{'#':<5} {'Entry':>12} {'Exit':>12} {'PnL':>12} {'Reason':<15}"
    separator = "-" * len(header)

    lines = [header, separator]

    for i, trade in enumerate(trades[:limit]):
        entry = trade.get("entry", 0)
        exit_price = trade.get("exit", 0)
        pnl = trade.get("pnl", 0)
        reason = trade.get("reason", "")

        line = (
            f"{i + 1:<5} {entry:>12.2f} {exit_price:>12.2f} {pnl:>+11.2f} {reason:<15}"
        )
        lines.append(line)

    if len(trades) > limit:
        lines.append(f"\n... and {len(trades) - limit} more trades")

    return "\n".join(lines)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers

    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if denominator is zero

    Returns:
        Division result or default
    """
    if denominator == 0:
        return default

    return numerator / denominator


def calculate_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change

    Args:
        old_value: Old value
        new_value: New value

    Returns:
        Percentage change
    """
    if old_value == 0:
        return 0.0

    return (new_value - old_value) / old_value * 100
