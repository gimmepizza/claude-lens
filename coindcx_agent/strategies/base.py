"""Base strategy interface for quant trading strategies."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import pandas as pd


class Signal(Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class TradeSignal:
    """A trading signal with metadata."""
    signal: Signal
    strategy: str
    confidence: float  # 0.0 to 1.0
    price: float
    reason: str
    indicators: dict


class Strategy(ABC):
    """Abstract base class for trading strategies."""

    name: str = "base"

    @abstractmethod
    def analyze(self, df: pd.DataFrame) -> TradeSignal:
        """Analyze market data and produce a trading signal.

        Args:
            df: OHLCV DataFrame with columns: time, open, high, low, close, volume

        Returns:
            TradeSignal with buy/sell/hold recommendation
        """
        ...

    def _current_price(self, df: pd.DataFrame) -> float:
        return float(df["close"].iloc[-1])
