import pandas as pd
import pytest

from coindcx_agent import indicators as ind
from coindcx_agent.strategies import STRATEGIES, get_strategy, to_daily
from .conftest import make_candles


@pytest.mark.parametrize("name", list(STRATEGIES))
def test_no_lookahead_daily(name, daily):
    """The target at bar k must not change when later bars are appended."""
    s = get_strategy(name, "1d")
    full = s.target(daily)
    for k in (300, 450, 700, 899):
        partial = s.target(daily.iloc[: k + 1])
        assert partial.iloc[-1] == pytest.approx(full.iloc[k]), f"{name} peeks ahead at bar {k}"


@pytest.mark.parametrize("name", ["ensemble", "donchian", "trend_vol"])
def test_no_lookahead_hourly_with_daily_signals(name):
    h = make_candles(n=24 * 400, freq="1h", vol=0.006, drift=0.0001)
    s = get_strategy(name, "1h")
    full = s.target(h)
    for k in (24 * 300 + 5, 24 * 350 + 23, len(h) - 1):
        assert s.target(h.iloc[: k + 1]).iloc[-1] == pytest.approx(full.iloc[k])


def test_daily_signal_changes_only_at_day_close():
    h = make_candles(n=24 * 300, freq="1h", vol=0.006, drift=0.0003)
    t = get_strategy("donchian", "1h").target(h)
    changes = t.index[t.diff().fillna(0) != 0]
    assert len(changes) > 0
    assert all(ts.hour == 23 for ts in changes)  # the bar that closes at 00:00 UTC


def test_hourly_daily_view_matches_daily_strategy():
    h = make_candles(n=24 * 300, freq="1h", vol=0.006, drift=0.0003)
    d = to_daily(h)
    th = get_strategy("ema_cross", "1h").target(h)
    td = get_strategy("ema_cross", "1d").target(d)
    for day in d.index[150:160]:
        assert th.loc[day + pd.Timedelta(hours=23)] == td.loc[day]


@pytest.mark.parametrize("name", list(STRATEGIES))
def test_targets_bounded(name, daily):
    t = get_strategy(name, "1d").target(daily)
    assert t.between(0, 1).all() and not t.isna().any()


def test_donchian_channel_excludes_current_bar(daily):
    hi, lo = ind.donchian(daily, 10)
    assert hi.iloc[20] == daily["high"].iloc[10:20].max()


def test_rsi_bounds(daily):
    r = ind.rsi(daily["close"]).dropna()
    assert r.between(0, 100).all()
