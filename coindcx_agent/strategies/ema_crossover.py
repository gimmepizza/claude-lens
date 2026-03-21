"""EMA Crossover strategy — classic trend-following approach."""

import pandas as pd

from ..utils.indicators import ema
from ..config import StrategyParams
from .base import Strategy, Signal, TradeSignal


class EMACrossoverStrategy(Strategy):
    """Exponential Moving Average crossover strategy.

    Generates BUY when fast EMA crosses above slow EMA,
    SELL when fast EMA crosses below slow EMA.
    """

    name = "ema_crossover"

    def __init__(self, params: StrategyParams):
        self.fast_period = params.ema_fast_period
        self.slow_period = params.ema_slow_period

    def analyze(self, df: pd.DataFrame) -> TradeSignal:
        price = self._current_price(df)
        fast = ema(df["close"], self.fast_period)
        slow = ema(df["close"], self.slow_period)

        fast_current = float(fast.iloc[-1])
        slow_current = float(slow.iloc[-1])
        fast_prev = float(fast.iloc[-2])
        slow_prev = float(slow.iloc[-2])

        indicators = {
            f"ema_{self.fast_period}": fast_current,
            f"ema_{self.slow_period}": slow_current,
            "spread": fast_current - slow_current,
        }

        # Bullish crossover
        if fast_prev <= slow_prev and fast_current > slow_current:
            spread_pct = abs(fast_current - slow_current) / slow_current
            confidence = min(spread_pct * 100, 1.0)
            return TradeSignal(
                signal=Signal.BUY,
                strategy=self.name,
                confidence=confidence,
                price=price,
                reason=f"EMA{self.fast_period} crossed above EMA{self.slow_period}",
                indicators=indicators,
            )

        # Bearish crossover
        if fast_prev >= slow_prev and fast_current < slow_current:
            spread_pct = abs(fast_current - slow_current) / slow_current
            confidence = min(spread_pct * 100, 1.0)
            return TradeSignal(
                signal=Signal.SELL,
                strategy=self.name,
                confidence=confidence,
                price=price,
                reason=f"EMA{self.fast_period} crossed below EMA{self.slow_period}",
                indicators=indicators,
            )

        # No crossover — hold
        direction = "bullish" if fast_current > slow_current else "bearish"
        return TradeSignal(
            signal=Signal.HOLD,
            strategy=self.name,
            confidence=0.0,
            price=price,
            reason=f"No crossover — trend is {direction}",
            indicators=indicators,
        )
