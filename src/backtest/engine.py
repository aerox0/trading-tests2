"""Backtest engine for running strategies"""

from ..core.base_backtest import BaseBacktest
from ..core.base_strategy import BaseStrategy
import pandas as pd
from typing import Dict, Any


class BacktestEngine(BaseBacktest):
    """Simple backtest engine for trading strategies"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.initial_capital = config.get("initial_capital", 10000.0)

    def run(self, df: pd.DataFrame, strategy: BaseStrategy) -> Dict[str, Any]:
        """Run backtest with given strategy and data

        Args:
            df: OHLCV data
            strategy: Strategy instance

        Returns:
            Dictionary with backtest results
        """
        # Validate data
        self.validate_data(df)

        # Reset strategy state
        strategy.reset_state()

        # Calculate indicators
        df = strategy.calculate_indicators(df)

        # Generate signals
        df = strategy.generate_signals(df)

        # Execute trades
        for i in range(len(df)):
            strategy.execute_trade(df, i)

        # Calculate metrics
        metrics = strategy.calculate_metrics()
        metrics["equity_curve"] = strategy.equity_curve
        metrics["trades"] = strategy.trades

        return metrics
