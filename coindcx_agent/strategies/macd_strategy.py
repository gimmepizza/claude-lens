"""MACD (Moving Average Convergence Divergence) strategy."""

import pandas as pd

from ..utils.indicators import macd
from ..config import StrategyParams
from .base import Strategy, Signal, TradeSignal


class MACDStrategy(Strategy):
    """MACD crossover strategy.

    BUY when MACD line crosses above signal line,
    SELL when MACD line crosses below signal line.
    """

    name = "macd"

    def __init__(self, params: StrategyParams):
        self.fast = params.macd_fast
        self.slow = params.macd_slow
        self.signal_period = params.macd_signal

    def analyze(self, df: pd.DataFrame) -> TradeSignal:
        price = self._current_price(df)
        macd_line, signal_line, histogram = macd(
            df["close"], self.fast, self.slow, self.signal_period
        )

        macd_current = float(macd_line.iloc[-1])
        signal_current = float(signal_line.iloc[-1])
        hist_current = float(histogram.iloc[-1])
        macd_prev = float(macd_line.iloc[-2])
        signal_prev = float(signal_line.iloc[-2])

        indicators = {
            "macd": macd_current,
            "signal": signal_current,
            "histogram": hist_current,
        }

        # Bullish crossover
        if macd_prev <= signal_prev and macd_current > signal_current:
            confidence = min(abs(hist_current) / price * 1000, 1.0)
            return TradeSignal(
                signal=Signal.BUY,
                strategy=self.name,
                confidence=max(confidence, 0.3),
                price=price,
                reason=f"MACD crossed above signal (hist: {hist_current:.4f})",
                indicators=indicators,
            )

        # Bearish crossover
        if macd_prev >= signal_prev and macd_current < signal_current:
            confidence = min(abs(hist_current) / price * 1000, 1.0)
            return TradeSignal(
                signal=Signal.SELL,
                strategy=self.name,
                confidence=max(confidence, 0.3),
                price=price,
                reason=f"MACD crossed below signal (hist: {hist_current:.4f})",
                indicators=indicators,
            )

        trend = "bullish" if hist_current > 0 else "bearish"
        return TradeSignal(
            signal=Signal.HOLD,
            strategy=self.name,
            confidence=0.0,
            price=price,
            reason=f"No MACD crossover — momentum is {trend}",
            indicators=indicators,
        )
