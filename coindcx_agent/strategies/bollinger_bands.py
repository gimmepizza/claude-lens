"""Bollinger Bands mean-reversion strategy."""

import pandas as pd

from ..utils.indicators import bollinger_bands
from ..config import StrategyParams
from .base import Strategy, Signal, TradeSignal


class BollingerBandsStrategy(Strategy):
    """Bollinger Bands mean-reversion strategy.

    BUY when price touches or drops below the lower band,
    SELL when price touches or rises above the upper band.
    """

    name = "bollinger_bands"

    def __init__(self, params: StrategyParams):
        self.period = params.bb_period
        self.std_dev = params.bb_std_dev

    def analyze(self, df: pd.DataFrame) -> TradeSignal:
        price = self._current_price(df)
        upper, middle, lower = bollinger_bands(df["close"], self.period, self.std_dev)

        upper_val = float(upper.iloc[-1])
        middle_val = float(middle.iloc[-1])
        lower_val = float(lower.iloc[-1])
        bandwidth = (upper_val - lower_val) / middle_val if middle_val else 0

        indicators = {
            "bb_upper": upper_val,
            "bb_middle": middle_val,
            "bb_lower": lower_val,
            "bandwidth": bandwidth,
        }

        # Price below lower band → BUY
        if price <= lower_val:
            distance = (lower_val - price) / lower_val if lower_val else 0
            confidence = min(distance * 10, 1.0)
            return TradeSignal(
                signal=Signal.BUY,
                strategy=self.name,
                confidence=max(confidence, 0.3),
                price=price,
                reason=f"Price ({price:.2f}) at/below lower BB ({lower_val:.2f})",
                indicators=indicators,
            )

        # Price above upper band → SELL
        if price >= upper_val:
            distance = (price - upper_val) / upper_val if upper_val else 0
            confidence = min(distance * 10, 1.0)
            return TradeSignal(
                signal=Signal.SELL,
                strategy=self.name,
                confidence=max(confidence, 0.3),
                price=price,
                reason=f"Price ({price:.2f}) at/above upper BB ({upper_val:.2f})",
                indicators=indicators,
            )

        return TradeSignal(
            signal=Signal.HOLD,
            strategy=self.name,
            confidence=0.0,
            price=price,
            reason=f"Price ({price:.2f}) within bands [{lower_val:.2f}, {upper_val:.2f}]",
            indicators=indicators,
        )
