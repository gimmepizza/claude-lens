"""Live / paper trading loop.

Every `poll_s` seconds: check the kill switches and the protective stop.
Once per *closed* signal candle: compute the strategy target, size it through the
risk manager, and trade the difference. Every decision and fill is persisted,
so a restart picks up exactly where it left off.
"""

from __future__ import annotations

import logging
import signal
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from . import indicators as ind
from .brokers import Broker
from .config import INTERVAL_SECONDS, AgentConfig
from .data import CandleStore
from .risk import RiskManager, RiskState
from .state import StateStore
from .strategies import Strategy

log = logging.getLogger(__name__)


class Engine:
    def __init__(self, cfg: AgentConfig, strategy: Strategy, broker: Broker, store: StateStore):
        self.cfg, self.broker, self.store = cfg, broker, store
        self.client = broker.client
        self.rules = broker.rules
        self.candles = CandleStore(self.client, cfg.data_dir)
        daily = strategy.daily_signals or strategy.interval == "1d"
        self.signal_interval = "1d" if daily else strategy.interval
        self.strategy = replace(strategy, interval=self.signal_interval, daily_signals=False)
        self.key = f"risk:{broker.mode}:{self.rules.symbol}"
        self.rm = RiskManager(cfg.risk, RiskState.from_dict(store.get(self.key, {})),
                              bar_seconds=INTERVAL_SECONDS[self.signal_interval])
        self._running = False
        self.last: dict = {}

    # ── pieces ─────────────────────────────────────────────────────

    def lookback_bars(self) -> int:
        return 400 if self.signal_interval == "1d" else self.cfg.trading.lookback

    def compute_signal(self) -> dict:
        df = self.candles.latest(self.rules.pair, self.signal_interval, self.lookback_bars())
        if len(df) < 60:
            raise RuntimeError(f"only {len(df)} candles available for {self.rules.pair}")
        target = float(self.strategy.target(df).iloc[-1])
        if self.signal_interval == "1d":
            atr = float(ind.atr(df, self.cfg.risk.atr_days).iloc[-1])
        else:
            atr = float(ind.daily_atr(df, self.cfg.risk.atr_days).iloc[-1])
        return {"bar": df.index[-1].isoformat(), "target": target, "atr": atr,
                "high": float(df["high"].iloc[-1]), "close": float(df["close"].iloc[-1]),
                "snapshot": self.strategy.snapshot(df)}

    def _save(self):
        self.store.set(self.key, self.rm.s.to_dict())

    def _flatten(self, reason: str, stopped: bool = False):
        h = self.broker.holdings()
        if h.qty > 0 and self.broker.sell(h.qty, reason):
            self.rm.on_exit(stopped=stopped)
            self.store.event("warn", f"flattened: {reason}")

    def kill_file(self) -> bool:
        return Path(self.cfg.trading.kill_switch_file).exists()

    # ── one cycle ──────────────────────────────────────────────────

    def step(self, force_decision: bool = False) -> dict:
        now = datetime.now(timezone.utc)
        h = self.broker.holdings()
        self.rm.update_equity(h.equity, now)

        if self.rm.s.halted:
            if h.qty > 0:
                self._flatten("kill_switch")
            self._save()
            return {"status": "halted", "reason": self.rm.s.halted}

        if h.qty > 0 and self.rm.stop_triggered(h.bid):
            log.warning("Stop hit at %.4f (stop %.4f)", h.bid, self.rm.s.stop_price)
            self._flatten("stop", stopped=True)
            h = self.broker.holdings()

        decided_bar = self.store.get(f"{self.key}:last_bar")
        sig = None
        bar_s = INTERVAL_SECONDS[self.signal_interval]
        due = decided_bar is None or now.timestamp() >= datetime.fromisoformat(decided_bar).timestamp() + 2 * bar_s + 15
        if due or force_decision:
            sig = self.compute_signal()
            if sig["bar"] != decided_bar or force_decision:
                self._decide(sig, h)
                self.store.set(f"{self.key}:last_bar", sig["bar"])
                h = self.broker.holdings()

        self.store.add_equity(self.rules.symbol, self.broker.mode, h.equity, h.cash, h.qty, h.bid,
                              sig["target"] if sig else -1)
        self._save()
        self.last = {"status": "ok", "equity": h.equity, "cash": h.cash, "qty": h.qty, "price": h.bid,
                     "exposure": h.exposure, "signal": sig, "risk": self.rm.s.to_dict()}
        return self.last

    def _decide(self, sig: dict, h):
        rm = self.rm
        if h.qty > 0:
            rm.on_bar(sig["high"], sig["atr"])
        rm.tick()
        want = rm.desired_fraction(sig["target"], h.bid, sig["atr"], h.exposure)
        cur_val, want_val = h.qty * h.bid, want * h.equity
        log.info("Signal bar %s: target=%.2f -> hold %.0f%% of equity (now %.0f%%)",
                 sig["bar"], sig["target"], want * 100, h.exposure * 100)
        if want <= 1e-9 and h.qty > 0:
            if self.broker.sell(h.qty, "signal"):
                rm.on_exit(stopped=False)
        elif want_val > cur_val + 1e-9:
            was_flat = h.qty <= 0
            if self.broker.buy(want_val - cur_val, "signal") and was_flat:
                rm.on_entry(self.broker.holdings().ask, sig["atr"])
        elif want_val < cur_val - 1e-9 and h.qty > 0:
            self.broker.sell((cur_val - want_val) / h.bid, "rebalance")

    # ── loop ───────────────────────────────────────────────────────

    def run(self):
        self._running = True

        def _stop(*_):
            log.info("Shutdown requested; finishing current step")
            self._running = False

        signal.signal(signal.SIGINT, _stop)
        signal.signal(signal.SIGTERM, _stop)
        self.store.event("info", f"start {self.broker.mode} {self.rules.symbol} {self.strategy.name}")
        errors = 0
        while self._running:
            if self.kill_file():
                log.error("Kill-switch file '%s' found: stopping (positions left as they are)",
                          self.cfg.trading.kill_switch_file)
                self.store.event("warn", "kill-switch file found; stopped")
                break
            try:
                r = self.step()
                errors = 0
                if r["status"] == "halted":
                    log.error("Trading halted: %s. Run `reset-halt` after reviewing.", r["reason"])
                    break
                log.info("equity=%.2f cash=%.2f qty=%.8f px=%.4f exposure=%.0f%%",
                         r["equity"], r["cash"], r["qty"], r["price"], r["exposure"] * 100)
            except Exception as e:  # keep running through transient API failures
                errors += 1
                log.exception("Step failed (%d in a row): %s", errors, e)
                self.store.event("error", str(e)[:500])
                if errors >= 10:
                    log.error("Too many consecutive errors; stopping")
                    break
            for _ in range(self.cfg.trading.poll_s * (2 ** min(errors, 4))):
                if not self._running:
                    break
                time.sleep(1)
        self._save()
        self.store.event("info", "stopped")
