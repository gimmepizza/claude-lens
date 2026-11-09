"""30 minute – 3 hour holding horizon: risk rules, backtest and engine."""

from dataclasses import dataclass
from typing import ClassVar

import pandas as pd
import pytest

from coindcx_agent.backtest import run_backtest
from coindcx_agent.brokers import PaperBroker
from coindcx_agent.config import AgentConfig, CostModel, RiskConfig
from coindcx_agent.engine import Engine
from coindcx_agent.risk import RiskManager
from coindcx_agent.state import StateStore
from coindcx_agent.strategies import INTRADAY_RISK, STRATEGIES, Strategy, apply_risk_defaults, get_strategy
from .conftest import make_candles
from .test_engine import FakeClient

FREE = CostModel(fee_pct=0, maker_fee_pct=0, slippage_pct=0, spread_pct=0, tds_pct=0)


def intraday_risk(**kw):
    r = RiskConfig(max_drawdown_pct=0, daily_loss_limit_pct=0)
    for k, v in {**INTRADAY_RISK, **kw}.items():
        setattr(r, k, v)
    return r


@pytest.fixture
def m15():
    return make_candles(n=4 * 24 * 60, freq="15min", vol=0.004, drift=0.00002)


def test_time_exit_caps_holding_at_3h(m15):
    t = pd.Series(1.0, index=m15.index)  # strategy would hold forever
    res = run_backtest(m15, t, "15m", FREE, intraday_risk(stop_atr_mult=0, take_profit_atr_mult=0))
    holds = [(tr.exit_time - tr.entry_time) for tr in res.trades if tr.exit_reason != "open"]
    assert holds and max(holds) <= pd.Timedelta(hours=3)
    assert {tr.exit_reason for tr in res.trades} <= {"time", "open"}
    # after a time exit the signal must reset first: a constant signal trades only once
    assert len(res.trades) == 1


def test_signal_exit_waits_for_min_hold(m15):
    t = pd.Series(0.0, index=m15.index)
    t.iloc[100] = 1.0  # one-bar blip
    res = run_backtest(m15, t, "15m", FREE, intraday_risk(stop_atr_mult=0, take_profit_atr_mult=0))
    tr = res.trades[0]
    assert tr.exit_reason == "signal"
    assert tr.exit_time - tr.entry_time == pd.Timedelta(minutes=30)


@pytest.mark.parametrize("name", [n for n, c in STRATEGIES.items() if c.kind == "intraday"])
def test_intraday_strategies_respect_horizon(name, m15):
    s = get_strategy(name)
    r = RiskConfig(max_drawdown_pct=0, daily_loss_limit_pct=0)
    apply_risk_defaults(s, r)
    res = run_backtest(m15, s.target(m15), "15m", FREE, r)
    for tr in res.trades:
        if tr.exit_reason == "open":
            continue
        hold = tr.exit_time - tr.entry_time
        assert hold <= pd.Timedelta(hours=3)
        if tr.exit_reason == "signal":
            assert hold >= pd.Timedelta(minutes=30)


def test_take_profit_fills_at_target():
    idx = pd.date_range("2024-01-01", periods=200, freq="15min", tz="UTC", name="time")
    df = pd.DataFrame({"open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0, "volume": 1.0}, index=idx)
    df.loc[idx[60], "high"] = 110.0
    t = pd.Series(0.0, index=idx)
    t.iloc[55:70] = 1.0
    res = run_backtest(df, t, "15m", FREE, intraday_risk(stop_atr_mult=0, take_profit_atr_mult=3, max_hold_hours=0))
    tp = [tr for tr in res.trades if tr.exit_reason == "take_profit"]
    # bar ATR is 1.0 (high - low), so the target is 100 + 3 * 1 = 103
    assert tp and tp[0].exit_price == pytest.approx(103.0, rel=1e-3)


def test_maker_entry_only_fills_when_price_trades_through():
    idx = pd.date_range("2024-01-01", periods=100, freq="15min", tz="UTC", name="time")
    df = pd.DataFrame({"open": 100.0, "high": 101.0, "low": 100.5, "close": 100.0, "volume": 1.0}, index=idx)
    # lows never go below the 100 close, so a resting bid at 100 never fills
    t = pd.Series(1.0, index=idx)
    costs = CostModel(fee_pct=0.1, maker_fee_pct=0, maker_entries=True, spread_pct=0, slippage_pct=0, tds_pct=0)
    res = run_backtest(df, t, "15m", costs, intraday_risk(stop_atr_mult=0, take_profit_atr_mult=0))
    assert res.metrics["trades"] == 0 and res.metrics["missed_maker_entries"] > 0
    df["low"] = 99.0
    res = run_backtest(df, t, "15m", costs, intraday_risk(stop_atr_mult=0, take_profit_atr_mult=0))
    assert res.trades and res.trades[0].entry_price == pytest.approx(100.0)
    assert res.metrics["fees"] > 0  # the taker exit still pays


def test_risk_min_hold_blocks_strategy_exit_not_stop():
    rm = RiskManager(intraday_risk(rebalance_threshold=0), bar_seconds=900)
    rm.on_entry(100, 1)
    rm.on_bar(100, 1)
    assert rm.desired_fraction(0, 100, 1, 0.9) == 0.9  # 15 min in: hold
    assert rm.stop_triggered(97)                        # stop still live
    rm.on_bar(100, 1)
    assert rm.desired_fraction(0, 100, 1, 0.9) == 0.0  # 30 min: may exit


def test_cli_applies_intraday_defaults_unless_overridden():
    from coindcx_agent.cli import build_config, build_parser
    cfg = build_config(build_parser().parse_args(["backtest", "-s", "breakout"]))
    assert cfg.trading.interval == "15m" and cfg.risk.max_hold_hours == 3 and cfg.risk.min_hold_hours == 0.5
    cfg = build_config(build_parser().parse_args(["backtest", "-s", "breakout", "--max-hold", "2"]))
    assert cfg.risk.max_hold_hours == 2
    cfg = build_config(build_parser().parse_args(["backtest", "-s", "ema_cross"]))
    assert cfg.trading.interval == "1h" and cfg.risk.max_hold_hours == 0


@dataclass
class Always(Strategy):
    name: ClassVar[str] = "always"
    interval: str = "15m"
    daily_signals: bool = False

    def _target(self, df):
        return pd.Series(1.0, index=df.index)


def test_engine_time_exit(tmp_path, rules):
    cfg = AgentConfig()
    cfg.data_dir = str(tmp_path)
    for k, v in intraday_risk(stop_atr_mult=0, take_profit_atr_mult=0).__dict__.items():
        setattr(cfg.risk, k, v)
    client = FakeClient(rules)
    start = (pd.Timestamp.now(tz="UTC").floor("15min") - pd.Timedelta(minutes=15 * 500)).tz_localize(None)
    client.df = make_candles(n=500, freq="15min", start=str(start)) * 75000
    store = StateStore(":memory:")
    eng = Engine(cfg, Always(), PaperBroker(cfg, client, rules, store), store)
    eng.step(force_decision=True)
    assert eng.broker.holdings().qty > 0
    for _ in range(11):
        eng.step(force_decision=True)
    assert eng.broker.holdings().qty > 0          # 11 bars = 2h45m: still holding
    eng.step(force_decision=True)
    assert eng.broker.holdings().qty == 0         # 12 bars = 3h: time exit
    assert store.fills()[0]["reason"] == "time"
    eng.step(force_decision=True)
    assert eng.broker.holdings().qty == 0         # no re-entry until the signal resets
