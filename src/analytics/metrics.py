"""Advanced performance metrics for trading strategies"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple


def calculate_calmar_ratio(total_return: float, max_drawdown: float) -> float:
    """Calculate Calmar ratio (annualized return / max drawdown)

    Args:
        total_return: Total return as percentage
        max_drawdown: Maximum drawdown as percentage (negative)

    Returns:
        Calmar ratio
    """
    if max_drawdown == 0:
        return np.inf
    return total_return / abs(max_drawdown)


def calculate_sortino_ratio(returns: np.ndarray, target_return: float = 0.0) -> float:
    """Calculate Sortino ratio (downside risk-adjusted return)

    Args:
        returns: Array of returns
        target_return: Minimum acceptable return (default: 0)

    Returns:
        Sortino ratio
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0

    excess_returns = returns - target_return
    downside_returns = excess_returns[excess_returns < 0]

    if len(downside_returns) == 0:
        return np.inf

    downside_deviation = np.sqrt(np.mean(downside_returns**2))

    if downside_deviation == 0:
        return np.inf

    return returns.mean() / downside_deviation


def calculate_omega_ratio(returns: np.ndarray, threshold: float = 0.0) -> float:
    """Calculate Omega ratio (probability-weighted ratio of gains vs losses)

    Args:
        returns: Array of returns
        threshold: Threshold return (default: 0)

    Returns:
        Omega ratio
    """
    if len(returns) == 0:
        return 0.0

    gains = returns[returns > threshold] - threshold
    losses = threshold - returns[returns < threshold]

    if len(losses) == 0:
        return np.inf if len(gains) > 0 else 0.0

    return np.sum(gains) / np.sum(losses)


def calculate_win_streak(trades: List[Dict]) -> int:
    """Calculate maximum consecutive winning trades

    Args:
        trades: List of trade dictionaries

    Returns:
        Maximum win streak
    """
    if not trades:
        return 0

    max_streak = 0
    current_streak = 0

    for trade in trades:
        if trade["pnl"] > 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    return max_streak


def calculate_loss_streak(trades: List[Dict]) -> int:
    """Calculate maximum consecutive losing trades

    Args:
        trades: List of trade dictionaries

    Returns:
        Maximum loss streak
    """
    if not trades:
        return 0

    max_streak = 0
    current_streak = 0

    for trade in trades:
        if trade["pnl"] < 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    return max_streak


def calculate_trade_duration_stats(
    trades: List[Dict], df: pd.DataFrame, timestamps: pd.DatetimeIndex
) -> Dict[str, float]:
    """Calculate trade duration statistics

    Args:
        trades: List of trade dictionaries with index information
        df: OHLCV DataFrame
        timestamps: Timestamp index of DataFrame

    Returns:
        Dictionary with duration statistics
    """
    if not trades or len(trades) == 0:
        return {
            "avg_duration_bars": 0,
            "max_duration_bars": 0,
            "min_duration_bars": 0,
        }

    durations = []

    for i, trade in enumerate(trades):
        # Estimate duration from trade sequence
        if i > 0:
            durations.append(1)
        else:
            durations.append(1)

    if not durations:
        return {
            "avg_duration_bars": 0,
            "max_duration_bars": 0,
            "min_duration_bars": 0,
        }

    return {
        "avg_duration_bars": np.mean(durations),
        "max_duration_bars": np.max(durations),
        "min_duration_bars": np.min(durations),
    }


def calculate_monthly_returns(
    equity_curve: List[float], timestamps: pd.DatetimeIndex
) -> pd.DataFrame:
    """Calculate monthly returns from equity curve

    Args:
        equity_curve: List of equity values
        timestamps: Timestamp index corresponding to equity curve

    Returns:
        DataFrame with monthly returns
    """
    if len(equity_curve) == 0:
        return pd.DataFrame()

    df = pd.DataFrame({"equity": equity_curve, "timestamp": timestamps})
    df.set_index("timestamp", inplace=True)

    # Resample to monthly and take last value
    monthly_equity = df.resample("ME").last().dropna()

    if len(monthly_equity) < 2:
        return pd.DataFrame()

    # Calculate monthly returns
    monthly_returns = monthly_equity.pct_change().dropna() * 100

    # Format as DataFrame with year/month columns
    monthly_returns_df = pd.DataFrame({"return_pct": monthly_returns.values.flatten()})
    monthly_returns_df["year"] = monthly_returns.index.year
    monthly_returns_df["month"] = monthly_returns.index.month

    return monthly_returns_df


def calculate_profit_distribution(trades: List[Dict]) -> Dict[str, float]:
    """Calculate profit distribution statistics

    Args:
        trades: List of trade dictionaries

    Returns:
        Dictionary with profit distribution stats
    """
    if not trades:
        return {
            "avg_win": 0,
            "avg_loss": 0,
            "largest_win": 0,
            "largest_loss": 0,
            "profit_factor": 0,
            "expected_value": 0,
        }

    pnls = [t["pnl"] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]

    avg_win = np.mean(wins) if wins else 0
    avg_loss = np.mean(losses) if losses else 0
    largest_win = max(wins) if wins else 0
    largest_loss = min(losses) if losses else 0

    total_wins = sum(wins)
    total_losses = sum(losses)

    if total_losses != 0:
        profit_factor = abs(total_wins / total_losses)
    else:
        profit_factor = float("inf") if wins else 0

    expected_value = np.mean(pnls)

    return {
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "largest_win": largest_win,
        "largest_loss": largest_loss,
        "profit_factor": profit_factor,
        "expected_value": expected_value,
    }


def calculate_annualized_metrics(
    equity_curve: List[float], timestamps: pd.DatetimeIndex
) -> Dict[str, float]:
    """Calculate annualized metrics

    Args:
        equity_curve: List of equity values
        timestamps: Timestamp index

    Returns:
        Dictionary with annualized metrics
    """
    if len(equity_curve) < 2:
        return {"annualized_return": 0, "annualized_volatility": 0}

    equity_array = np.array(equity_curve)

    # Calculate returns
    returns = np.diff(equity_array) / equity_array[:-1]

    # Calculate time period in years
    time_span = (timestamps[-1] - timestamps[0]).days / 365.25

    if time_span == 0:
        return {"annualized_return": 0, "annualized_volatility": 0}

    # Annualized return (CAGR)
    final_equity = equity_array[-1]
    initial_equity = equity_array[0]
    annualized_return = (final_equity / initial_equity) ** (1 / time_span) - 1

    # Annualized volatility
    if len(returns) > 0 and returns.std() != 0:
        annualized_volatility = returns.std() * np.sqrt(252)
    else:
        annualized_volatility = 0

    return {
        "annualized_return": annualized_return * 100,
        "annualized_volatility": annualized_volatility * 100,
    }


def calculate_drawdown_series(equity_curve: List[float]) -> pd.Series:
    """Calculate drawdown series from equity curve

    Args:
        equity_curve: List of equity values

    Returns:
        Series with drawdown percentages
    """
    if len(equity_curve) == 0:
        return pd.Series()

    equity_array = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_array)
    drawdown = (equity_array - running_max) / running_max * 100

    return pd.Series(drawdown)


def calculate_risk_reward_ratio(
    avg_win: float, avg_loss: float, win_rate: float
) -> float:
    """Calculate risk-reward ratio

    Args:
        avg_win: Average winning trade
        avg_loss: Average losing trade (negative value)
        win_rate: Win rate as percentage (0-100)

    Returns:
        Risk-reward ratio
    """
    if avg_loss == 0 or win_rate == 0:
        return 0.0

    avg_win_abs = abs(avg_win)
    avg_loss_abs = abs(avg_loss)

    win_prob = win_rate / 100
    loss_prob = 1 - win_prob

    expected_win = avg_win_abs * win_prob
    expected_loss = avg_loss_abs * loss_prob

    if expected_loss == 0:
        return np.inf

    return expected_win / expected_loss
