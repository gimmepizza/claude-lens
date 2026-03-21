"""RSI Mean-Reversion strategy."""

import pandas as pd

from ..utils.indicators import rsi
from ..config import StrategyParams
from .base import Strategy, Signal, TradeSignal


class RSIStrategy(Strategy):
    """Relative Strength Index mean-reversion strategy.

    BUY when RSI drops below oversold threshold,
    SELL when RSI rises above overbought threshold.
    """

    name = "rsi"

    def __init__(self, params: StrategyParams):
        self.period = params.rsi_period
        self.overbought = params.rsi_overbought
        self.oversold = params.rsi_oversold

    def analyze(self, df: pd.DataFrame) -> TradeSignal:
        price = self._current_price(df)
        rsi_values = rsi(df["close"], self.period)
        current_rsi = float(rsi_values.iloc[-1])
        prev_rsi = float(rsi_values.iloc[-2])

        indicators = {
            "rsi": current_rsi,
            "rsi_prev": prev_rsi,
            "overbought": self.overbought,
            "oversold": self.oversold,
        }

        # Oversold → BUY
        if current_rsi < self.oversold:
            confidence = (self.oversold - current_rsi) / self.oversold
            return TradeSignal(
                signal=Signal.BUY,
                strategy=self.name,
                confidence=min(confidence, 1.0),
                price=price,
                reason=f"RSI oversold at {current_rsi:.1f} (< {self.oversold})",
                indicators=indicators,
            )

        # Overbought → SELL
        if current_rsi > self.overbought:
            confidence = (current_rsi - self.overbought) / (100 - self.overbought)
            return TradeSignal(
                signal=Signal.SELL,
                strategy=self.name,
                confidence=min(confidence, 1.0),
                price=price,
                reason=f"RSI overbought at {current_rsi:.1f} (> {self.overbought})",
                indicators=indicators,
            )

        return TradeSignal(
            signal=Signal.HOLD,
            strategy=self.name,
            confidence=0.0,
            price=price,
            reason=f"RSI neutral at {current_rsi:.1f}",
            indicators=indicators,
        )
