"""Abstract base class for all trading strategies"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies

    All strategies must inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize strategy with configuration

        Args:
            config: Strategy configuration dictionary
        """
        self.config = config
        self.name = config.get("name", self.__class__.__name__)

        # Trading state
        self.position = None
        self.entry_price = None
        self.position_size = 0.0
        self.stop_loss = None
        self.take_profit = None
        self.trades = []
        self.equity_curve = []

        # Capital management
        self.capital = config.get("initial_capital", 10000.0)
        self.initial_capital = self.capital

    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all indicators required by the strategy

        Args:
            df: OHLCV data

        Returns:
            DataFrame with added indicator columns
        """
        pass

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate entry and exit signals

        Args:
            df: DataFrame with indicators

        Returns:
            DataFrame with signal columns (long_signal, short_signal, etc.)
        """
        pass

    @abstractmethod
    def execute_trade(self, df: pd.DataFrame, index: int) -> Optional[Dict]:
        """Execute trade logic for a specific bar

        Args:
            df: DataFrame with indicators and signals
            index: Current bar index

        Returns:
            Trade dictionary if trade executed, None otherwise
        """
        pass

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate strategy configuration

        Args:
            config: Configuration to validate

        Returns:
            True if valid, raises ValueError if invalid
        """
        required_keys = ["ema_fast", "ema_slow", "atr_period"]

        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")

        if config["ema_fast"] >= config["ema_slow"]:
            raise ValueError("ema_fast must be less than ema_slow")

        return True

    def reset_state(self):
        """Reset strategy state for new backtest"""
        self.position = None
        self.entry_price = None
        self.position_size = 0.0
        self.stop_loss = None
        self.take_profit = None
        self.trades = []
        self.equity_curve = []
        self.capital = self.initial_capital

    def get_position_size(self, price: float, position_pct: float) -> float:
        """Calculate position size based on capital and percentage

        Args:
            price: Current price
            position_pct: Percentage of capital to allocate

        Returns:
            Number of units to trade
        """
        return self.capital * position_pct / price

    def close_position(self, exit_price: float, reason: str) -> Dict:
        """Close current position and record trade

        Args:
            exit_price: Exit price
            reason: Exit reason (SL, TP, Trend Change, etc.)

        Returns:
            Trade dictionary
        """
        if self.position == "long":
            pnl = (exit_price - self.entry_price) * self.position_size
        elif self.position == "short":
            pnl = (self.entry_price - exit_price) * self.position_size
        else:
            raise ValueError("No position to close")

        self.capital += pnl

        trade = {
            "entry": self.entry_price,
            "exit": exit_price,
            "pnl": pnl,
            "reason": reason,
            "type": self.position,
            "pnl_pct": (pnl / (self.entry_price * self.position_size)) * 100,
        }

        self.trades.append(trade)

        self.position = None
        self.entry_price = None
        self.position_size = 0.0
        self.stop_loss = None
        self.take_profit = None

        return trade

    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics from backtest results

        Returns:
            Dictionary of performance metrics
        """
        if not self.trades:
            return {
                "total_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "total_trades": 0,
                "win_rate": 0.0,
                "final_capital": self.capital,
            }

        # Calculate returns
        returns = np.diff(self.equity_curve) / np.array(self.equity_curve[:-1])

        # Sharpe ratio
        if len(returns) > 1 and returns.std() != 0:
            sharpe = (returns.mean() / returns.std()) * (len(returns) ** 0.5)
        else:
            sharpe = 0.0

        # Max drawdown
        equity_array = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max * 100
        max_drawdown = drawdown.min()

        # Win rate
        win_rate = sum(1 for t in self.trades if t["pnl"] > 0) / len(self.trades) * 100

        # Total return
        total_return = (
            (self.capital - self.initial_capital) / self.initial_capital * 100
        )

        # Profit factor
        winning_trades = [t["pnl"] for t in self.trades if t["pnl"] > 0]
        losing_trades = [t["pnl"] for t in self.trades if t["pnl"] < 0]

        if losing_trades:
            profit_factor = sum(winning_trades) / abs(sum(losing_trades))
        else:
            profit_factor = float("inf") if winning_trades else 0.0

        # Average trade
        avg_trade = np.mean([t["pnl"] for t in self.trades])

        return {
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "total_trades": len(self.trades),
            "win_rate": win_rate,
            "final_capital": self.capital,
            "profit_factor": profit_factor,
            "avg_trade": avg_trade,
            "total_pnl": sum(t["pnl"] for t in self.trades),
        }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name={self.name}, capital={self.capital:.2f})"
        )
