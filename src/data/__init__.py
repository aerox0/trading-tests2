"""Data fetching and processing"""

from .fetcher import DataFetcher
from .splitter import TrainTestSplitter

__all__ = ["DataFetcher", "TrainTestSplitter"]
