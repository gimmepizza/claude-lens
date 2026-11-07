"""Engine + brokers against a fake exchange (no network)."""

from dataclasses import dataclass
from typing import ClassVar

import pandas as pd
import pytest

from coindcx_agent.brokers import LiveBroker, PaperBroker
from coindcx_agent.config import AgentConfig
from coindcx_agent.engine import Engine
from coindcx_agent.exchange import CoinDCXError
from coindcx_agent.state import StateStore
from coindcx_agent.strategies import Strategy
from .conftest import make_candles


@dataclass
class FixedTarget(Strategy):
    name: ClassVar[str] = "fixed"
    value: float = 1.0
    interval: str = "1d"

    def _target(self, df):
        return pd.Series(self.value, index=df.index)


class FakeClient:
    def __init__(self, rules, price=7_500_000.0, balances=None):
        self._rules, self.price = rules, price
        self.df = make_candles(n=500, start="2025-01-01") * 75000
        self.bal = balances or {"INR": {"free": 20000.0, "locked": 0.0}, "BTC": {"free": 0.5, "locked": 0.0}}
        self.orders, self.fail_create = {}, False

    def rules(self, symbol):
        return self._rules

    def best_bid_ask(self, pair):
        return self.price * 0.999, self.price * 1.001

    def candles(self, pair, interval, limit=1000, start_ms=None, end_ms=None):
        d = self.df
        if start_ms is not None:
            d = d[(d.index >= pd.to_datetime(start_ms, unit="ms", utc=True)) &
                  (d.index <= pd.to_datetime(end_ms, unit="ms", utc=True))]
        return [{"time": int(t.timestamp() * 1000), **r} for t, r in d.tail(limit).to_dict("index").items()]

    def balances(self):
        return self.bal

    def create_order(self, symbol, side, qty, price, order_type, cid):
        if self.fail_create:
            raise CoinDCXError(502, "bad gateway")
        oid = f"o{len(self.orders)}"
        self.orders[oid] = {"id": oid, "status": "filled", "total_quantity": qty, "remaining_quantity": 0,
                            "avg_price": price, "fee_amount": qty * price * 0.005, "side": side}
        if side == "buy":
            self.bal["INR"]["free"] -= qty * price * 1.005
            self.bal["BTC"]["free"] += qty
        else:
            self.bal["INR"]["free"] += qty * price * 0.995
            self.bal["BTC"]["free"] -= qty
        return self.orders[oid]

    def order_status(self, order_id=None, client_order_id=None):
        if order_id is None:
            raise CoinDCXError(404, "not found")
        return self.orders[order_id]

    def cancel_order(self, oid):
        return {}


def _cfg(tmp_path):
    cfg = AgentConfig()
    cfg.data_dir = str(tmp_path)
    cfg.trading.capital_limit = 10000
    cfg.risk.max_order_value = 100000
    cfg.risk.max_drawdown_pct = 35
    return cfg


def test_paper_buys_then_sells_and_persists(tmp_path, rules):
    cfg, client = _cfg(tmp_path), None
    client = FakeClient(rules)
    store = StateStore(str(tmp_path / "s.db"))
    eng = Engine(cfg, FixedTarget(value=1.0), PaperBroker(cfg, client, rules, store), store)
    r = eng.step(force_decision=True)
    assert r["qty"] > 0 and r["exposure"] > 0.95
    assert store.fills()[0]["side"] == "buy"

    # restart with a flat target: state is reloaded and the position is sold
    store2 = StateStore(str(tmp_path / "s.db"))
    eng2 = Engine(cfg, FixedTarget(value=0.0), PaperBroker(cfg, client, rules, store2), store2)
    assert eng2.broker.holdings().qty == r["qty"]
    r2 = eng2.step(force_decision=True)
    assert r2["qty"] == 0 and store2.fills()[0]["side"] == "sell"
    assert store2.fills()[0]["tds"] > 0


def test_no_redecision_within_same_bar(tmp_path, rules):
    cfg, client = _cfg(tmp_path), FakeClient(rules)
    store = StateStore(":memory:")
    eng = Engine(cfg, FixedTarget(value=1.0), PaperBroker(cfg, client, rules, store), store)
    eng.step()
    n = len(store.fills())
    eng.step()
    assert len(store.fills()) == n


def test_live_never_sells_preexisting_coins(tmp_path, rules):
    cfg, client = _cfg(tmp_path), FakeClient(rules)
    store = StateStore(":memory:")
    live = LiveBroker(cfg, client, rules, store)
    h = live.holdings()
    assert h.qty == 0  # user's 0.5 BTC is not the bot's
    assert h.cash == 10000  # capital_limit respected
    eng = Engine(cfg, FixedTarget(value=1.0), live, store)
    eng.step(force_decision=True)
    bought = live.bot_qty()
    assert 0 < bought < 0.0014
    eng2 = Engine(cfg, FixedTarget(value=0.0), live, store)
    eng2.step(force_decision=True)
    assert live.bot_qty() == 0
    assert client.bal["BTC"]["free"] == pytest.approx(0.5)  # original holdings untouched


def test_live_create_failure_is_not_retried_blindly(tmp_path, rules):
    cfg, client = _cfg(tmp_path), FakeClient(rules)
    client.fail_create = True
    store = StateStore(":memory:")
    live = LiveBroker(cfg, client, rules, store)
    assert live.buy(5000, "test") is None
    assert live.bot_qty() == 0 and not client.orders


def test_max_order_value_caps_buys(tmp_path, rules):
    cfg, client = _cfg(tmp_path), FakeClient(rules)
    cfg.risk.max_order_value = 1000
    store = StateStore(":memory:")
    f = PaperBroker(cfg, client, rules, store).buy(50000, "test")
    assert f.qty * f.price <= 1000


def test_kill_switch_flattens(tmp_path, rules):
    cfg, client = _cfg(tmp_path), FakeClient(rules)
    store = StateStore(":memory:")
    eng = Engine(cfg, FixedTarget(value=1.0), PaperBroker(cfg, client, rules, store), store)
    eng.step(force_decision=True)
    client.price *= 0.5
    r = eng.step()
    assert r["status"] == "halted"
    assert eng.broker.holdings().qty == 0
