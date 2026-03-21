"""VWAP (Volume Weighted Average Price) strategy."""

import pandas as pd

from ..utils.indicators import vwap
from ..config import StrategyParams
from .base import Strategy, Signal, TradeSignal


class VWAPStrategy(Strategy):
    """VWAP-based trading strategy.

    BUY when price is significantly below VWAP (undervalued),
    SELL when price is significantly above VWAP (overvalued).
    """

    name = "vwap"

    def __init__(self, params: StrategyParams):
        self.deviation_threshold = params.vwap_deviation

    def analyze(self, df: pd.DataFrame) -> TradeSignal:
        price = self._current_price(df)
        vwap_values = vwap(df)
        current_vwap = float(vwap_values.iloc[-1])

        deviation_pct = ((price - current_vwap) / current_vwap) * 100 if current_vwap else 0

        indicators = {
            "vwap": current_vwap,
            "price": price,
            "deviation_pct": deviation_pct,
        }

        # Price significantly below VWAP → BUY
        if deviation_pct < -self.deviation_threshold:
            confidence = min(abs(deviation_pct) / (self.deviation_threshold * 3), 1.0)
            return TradeSignal(
                signal=Signal.BUY,
                strategy=self.name,
                confidence=confidence,
                price=price,
                reason=f"Price {deviation_pct:.2f}% below VWAP ({current_vwap:.2f})",
                indicators=indicators,
            )

        # Price significantly above VWAP → SELL
        if deviation_pct > self.deviation_threshold:
            confidence = min(abs(deviation_pct) / (self.deviation_threshold * 3), 1.0)
            return TradeSignal(
                signal=Signal.SELL,
                strategy=self.name,
                confidence=confidence,
                price=price,
                reason=f"Price {deviation_pct:.2f}% above VWAP ({current_vwap:.2f})",
                indicators=indicators,
            )

        return TradeSignal(
            signal=Signal.HOLD,
            strategy=self.name,
            confidence=0.0,
            price=price,
            reason=f"Price near VWAP ({deviation_pct:+.2f}%)",
            indicators=indicators,
        )
