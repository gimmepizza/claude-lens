"""Risk management shared by the backtester and the live engine.

Turns a strategy's target exposure into the fraction of equity to actually hold,
and owns protective state: ATR trailing stop, cooldown after a stop-out, daily
loss limit and a max-drawdown kill switch.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

from .config import RiskConfig

log = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))


@dataclass
class RiskState:
    peak_equity: float = 0.0
    day: str = ""
    day_start_equity: float = 0.0
    halted: str = ""          # permanent (kill switch) until reset by a human
    day_halted: bool = False  # no new buying for the rest of the IST day
    entry_price: float = 0.0
    stop_price: float = 0.0
    highest: float = 0.0
    cooldown: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "RiskState":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class RiskManager:
    def __init__(self, cfg: RiskConfig, state: RiskState | None = None, bar_seconds: int = 3600):
        self.cfg = cfg
        self.s = state or RiskState()
        self.cooldown_bars = max(0, int(round(cfg.cooldown_hours * 3600 / bar_seconds)))

    # ── equity guards ──────────────────────────────────────────────

    def update_equity(self, equity: float, ts: datetime) -> None:
        s, c = self.s, self.cfg
        day = ts.astimezone(IST).date().isoformat()
        if day != s.day:
            s.day, s.day_start_equity, s.day_halted = day, equity, False
        s.peak_equity = max(s.peak_equity, equity)

        if c.daily_loss_limit_pct > 0 and s.day_start_equity > 0 and not s.day_halted:
            if equity <= s.day_start_equity * (1 - c.daily_loss_limit_pct / 100):
                s.day_halted = True
                log.warning("Daily loss limit hit (%.1f%%): no new entries until tomorrow (IST)",
                            c.daily_loss_limit_pct)

        if c.max_drawdown_pct > 0 and not s.halted and s.peak_equity > 0:
            dd = 1 - equity / s.peak_equity
            if dd >= c.max_drawdown_pct / 100:
                s.halted = f"max drawdown {dd:.1%} at {ts.isoformat()}"
                log.error("KILL SWITCH: %s. Flattening and halting.", s.halted)

    # ── stops ──────────────────────────────────────────────────────

    @property
    def uses_stop(self) -> bool:
        return self.cfg.stop_atr_mult > 0

    def on_entry(self, price: float, atr: float) -> None:
        s = self.s
        s.entry_price = s.highest = price
        s.stop_price = price - self.cfg.stop_atr_mult * atr if self.uses_stop and atr > 0 else 0.0

    def on_bar(self, high: float, atr: float) -> None:
        """Ratchet the trailing stop after a bar closes while in a position."""
        s = self.s
        if not s.entry_price:
            return
        s.highest = max(s.highest, high)
        if self.uses_stop and self.cfg.trailing_stop and atr > 0:
            s.stop_price = max(s.stop_price, s.highest - self.cfg.stop_atr_mult * atr)

    def stop_triggered(self, low: float) -> bool:
        return bool(self.s.entry_price and self.s.stop_price and low <= self.s.stop_price)

    def on_exit(self, stopped: bool) -> None:
        s = self.s
        s.entry_price = s.stop_price = s.highest = 0.0
        if stopped:
            s.cooldown = self.cooldown_bars

    def tick(self) -> None:
        """Call once per closed bar."""
        if self.s.cooldown > 0:
            self.s.cooldown -= 1

    # ── sizing ─────────────────────────────────────────────────────

    def max_fraction(self, price: float, atr: float) -> float:
        """Largest equity fraction allowed, so a stop-out loses ~risk_per_trade_pct."""
        cap = self.cfg.max_position_pct / 100
        if self.uses_stop and atr > 0 and price > 0:
            stop_dist = self.cfg.stop_atr_mult * atr / price
            cap = min(cap, (self.cfg.risk_per_trade_pct / 100) / stop_dist)
        return max(cap, 0.0)

    def desired_fraction(self, target: float, price: float, atr: float, current: float) -> float:
        """Fraction of equity to hold in the asset after this bar."""
        s = self.s
        if s.halted:
            return 0.0
        want = max(0.0, min(1.0, target)) * self.max_fraction(price, atr)
        if want <= 1e-9:
            return 0.0
        if current <= 1e-9 and s.cooldown > 0:
            return 0.0
        if s.day_halted and want > current:
            return current  # may reduce, may not add
        # Don't churn fees on small adjustments.
        if current > 1e-9 and abs(want - current) < self.cfg.rebalance_threshold * max(want, current):
            return current
        return want
