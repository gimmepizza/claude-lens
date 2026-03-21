"""Composite strategy that combines signals from multiple strategies."""

import pandas as pd

from ..config import StrategyParams
from .base import Strategy, Signal, TradeSignal
from .ema_crossover import EMACrossoverStrategy
from .rsi_strategy import RSIStrategy
from .bollinger_bands import BollingerBandsStrategy
from .vwap_strategy import VWAPStrategy
from .macd_strategy import MACDStrategy


class CompositeStrategy(Strategy):
    """Combines multiple strategy signals using a voting/weighting system.

    Only generates a signal when multiple strategies agree, reducing
    false positives and increasing trade quality.
    """

    name = "composite"

    def __init__(self, params: StrategyParams, min_agreement: int = 3):
        self.strategies: list[Strategy] = [
            EMACrossoverStrategy(params),
            RSIStrategy(params),
            BollingerBandsStrategy(params),
            VWAPStrategy(params),
            MACDStrategy(params),
        ]
        self.min_agreement = min_agreement

    def analyze(self, df: pd.DataFrame) -> TradeSignal:
        price = float(df["close"].iloc[-1])
        signals = []

        for strategy in self.strategies:
            try:
                signal = strategy.analyze(df)
                signals.append(signal)
            except Exception:
                continue

        buy_signals = [s for s in signals if s.signal == Signal.BUY]
        sell_signals = [s for s in signals if s.signal == Signal.SELL]

        all_indicators = {}
        for s in signals:
            all_indicators[s.strategy] = {
                "signal": s.signal.value,
                "confidence": s.confidence,
                "reason": s.reason,
            }

        if len(buy_signals) >= self.min_agreement:
            avg_confidence = sum(s.confidence for s in buy_signals) / len(buy_signals)
            reasons = [s.reason for s in buy_signals]
            return TradeSignal(
                signal=Signal.BUY,
                strategy=self.name,
                confidence=avg_confidence,
                price=price,
                reason=f"{len(buy_signals)}/{len(signals)} strategies agree: BUY | " + "; ".join(reasons),
                indicators=all_indicators,
            )

        if len(sell_signals) >= self.min_agreement:
            avg_confidence = sum(s.confidence for s in sell_signals) / len(sell_signals)
            reasons = [s.reason for s in sell_signals]
            return TradeSignal(
                signal=Signal.SELL,
                strategy=self.name,
                confidence=avg_confidence,
                price=price,
                reason=f"{len(sell_signals)}/{len(signals)} strategies agree: SELL | " + "; ".join(reasons),
                indicators=all_indicators,
            )

        return TradeSignal(
            signal=Signal.HOLD,
            strategy=self.name,
            confidence=0.0,
            price=price,
            reason=f"No consensus — {len(buy_signals)} buy, {len(sell_signals)} sell, {len(signals) - len(buy_signals) - len(sell_signals)} hold",
            indicators=all_indicators,
        )
