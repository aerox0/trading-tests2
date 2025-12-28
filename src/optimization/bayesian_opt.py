"""Bayesian optimization using Optuna"""

import optuna
import pandas as pd
from typing import Dict, Any, Callable
from ..strategies import TrendFollowingStrategy
from ..backtest import BacktestEngine


class BayesianOptimizer:
    """Bayesian optimization using Optuna

    Most efficient method for high-dimensional parameter spaces.
    Uses Gaussian Process to model performance surface.
    """

    def __init__(
        self,
        strategy_class,
        df: pd.DataFrame,
        engine_config: Dict[str, Any],
        n_trials: int = 100,
    ):
        """Initialize Bayesian optimizer

        Args:
            strategy_class: Strategy class to optimize
            df: OHLCV data
            engine_config: Backtest engine configuration
            n_trials: Number of optimization trials
        """
        self.strategy_class = strategy_class
        self.df = df
        self.engine_config = engine_config
        self.n_trials = n_trials

    def optimize(self, direction: str = "maximize") -> Dict[str, Any]:
        """Run Bayesian optimization

        Args:
            direction: 'maximize' or 'minimize' objective

        Returns:
            Dictionary with best parameters and results
        """

        def objective(trial):
            # Define search space
            ema_fast = trial.suggest_int("ema_fast", 20, 100)
            ema_slow = trial.suggest_int("ema_slow", ema_fast + 20, 300)
            atr_sl = trial.suggest_float("atr_multiplier_sl", 0.3, 1.0)
            atr_tp = trial.suggest_float("atr_multiplier_tp", atr_sl * 2, 5.0)
            rsi_period = trial.suggest_int("rsi_period", 5, 25)
            volume_mult = trial.suggest_float("volume_multiplier", 0.8, 2.0)
            pos_size = trial.suggest_float("position_size_pct", 0.3, 0.8)

            # Strategy config
            config = {
                "ema_fast": ema_fast,
                "ema_slow": ema_slow,
                "atr_period": 14,
                "atr_multiplier_sl": atr_sl,
                "atr_multiplier_tp": atr_tp,
                "rsi_period": rsi_period,
                "volume_multiplier": volume_mult,
                "position_size_pct": pos_size,
                "initial_capital": self.engine_config.get("initial_capital", 10000),
            }

            # Run backtest
            strategy = self.strategy_class(config)
            engine = BacktestEngine(self.engine_config)
            results = engine.run(self.df, strategy)

            # Return objective (Sharpe ratio)
            if direction == "maximize":
                return results["sharpe_ratio"]
            else:
                return -results["sharpe_ratio"]

        # Create study
        study = optuna.create_study(direction="maximize")

        # Optimize
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=True)

        # Get best results
        best_params = study.best_params
        best_value = study.best_value

        # Run final backtest with best params
        final_config = {
            **best_params,
            "atr_period": 14,
            "initial_capital": self.engine_config.get("initial_capital", 10000),
        }

        strategy = self.strategy_class(final_config)
        engine = BacktestEngine(self.engine_config)
        final_results = engine.run(self.df, strategy)

        return {
            "best_params": best_params,
            "best_objective": best_value,
            "backtest_results": final_results,
            "n_trials": self.n_trials,
            "study": study,
        }

    def get_parameter_importance(self) -> Dict[str, float]:
        """Get importance of each parameter (if using latest trial)"""
        return {}
