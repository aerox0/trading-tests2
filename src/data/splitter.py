"""Train/test split utilities"""

import pandas as pd
from typing import Tuple, List
from enum import Enum


class SplitMethod(Enum):
    """Data splitting methods"""

    SEQUENTIAL = "sequential"  # First X% train, rest test
    RANDOM = "random"  # Random sampling
    TIME_SERIES = "time_series"  # Respect temporal order with sliding windows


class TrainTestSplitter:
    """Split data into training and testing sets"""

    @staticmethod
    def split_sequential(
        df: pd.DataFrame, train_pct: float = 0.7
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Split data sequentially (first part train, rest test)

        Args:
            df: Input DataFrame
            train_pct: Percentage for training set (default: 0.7)

        Returns:
            Tuple of (train_df, test_df)
        """
        split_idx = int(len(df) * train_pct)
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()

        print(f"Train: {len(train_df)} bars ({len(train_df) / len(df) * 100:.1f}%)")
        print(f"Test: {len(test_df)} bars ({len(test_df) / len(df) * 100:.1f}%)")

        return train_df, test_df

    @staticmethod
    def split_windows(
        df: pd.DataFrame, train_size: int = 500, test_size: int = 100, step: int = 100
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """Create sliding window train/test splits for walk-forward analysis

        Args:
            df: Input DataFrame
            train_size: Number of bars for training
            test_size: Number of bars for testing
            step: Step size for windows

        Returns:
            List of (train_df, test_df) tuples
        """
        splits = []
        total_length = train_size + test_size

        if len(df) < total_length:
            raise ValueError(
                f"DataFrame too short for {train_size} train + {test_size} test "
                f"(need {total_length}, have {len(df)})"
            )

        start_idx = 0
        while start_idx + total_length <= len(df):
            train_end = start_idx + train_size
            test_end = train_end + test_size

            train_df = df.iloc[start_idx:train_end].copy()
            test_df = df.iloc[train_end:test_end].copy()

            splits.append((train_df, test_df))

            start_idx += step

        print(f"Created {len(splits)} walk-forward windows")
        return splits

    @staticmethod
    def split_k_fold(
        df: pd.DataFrame, n_folds: int = 5
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """Create K-fold splits (for time series, use sequential folds)

        Args:
            df: Input DataFrame
            n_folds: Number of folds

        Returns:
            List of (train_df, test_df) tuples
        """
        fold_size = len(df) // n_folds
        splits = []

        for i in range(n_folds):
            test_start = i * fold_size
            test_end = (i + 1) * fold_size if i < n_folds - 1 else len(df)

            # Train = all except test fold
            train_df = pd.concat([df.iloc[:test_start], df.iloc[test_end:]]).copy()
            test_df = df.iloc[test_start:test_end].copy()

            splits.append((train_df, test_df))

        print(f"Created {len(splits)} K-fold splits")
        return splits
