import pandas as pd
import pytest

from coindcx_agent.backtest import run_backtest, walk_forward
from coindcx_agent.config import CostModel, RiskConfig
from coindcx_agent.strategies import get_strategy

FREE = CostModel(fee_pct=0, slippage_pct=0, spread_pct=0, tds_pct=0)
LOOSE = RiskConfig(stop_atr_mult=0, max_drawdown_pct=0, daily_loss_limit_pct=0, max_position_pct=100,
                   rebalance_threshold=0)


def test_zero_cost_matches_vectorized(daily):
    t = get_strategy("donchian", "1d").target(daily)
    t.iloc[-3:] = 0.0  # finish flat so equity is comparable open-to-open
    assert t.sum() > 50
    res = run_backtest(daily, t, "1d", FREE, LOOSE)
    ret = daily["open"].shift(-1) / daily["open"] - 1
    vec = (1 + t.shift(1).fillna(0) * ret).cumprod()
    assert res.metrics["total_return"] == pytest.approx(vec.iloc[-2] - 1, rel=1e-6)


def test_costs_reduce_returns(daily):
    t = get_strategy("donchian", "1d").target(daily)
    free = run_backtest(daily, t, "1d", FREE, LOOSE).metrics["total_return"]
    costly = run_backtest(daily, t, "1d", CostModel(), LOOSE).metrics
    assert costly["total_return"] < free
    assert costly["fees"] > 0 and costly["tds_withheld"] > 0


def test_always_in_equals_buy_and_hold_without_costs(daily):
    t = pd.Series(1.0, index=daily.index)
    m = run_backtest(daily, t, "1d", FREE, LOOSE).metrics
    # enters at bar 1's open; benchmark at bar 0's open
    expected = daily["close"].iloc[-1] / daily["open"].iloc[1] - 1
    assert m["total_return"] == pytest.approx(expected, rel=1e-9)


def test_gap_through_stop_fills_at_open():
    idx = pd.date_range("2024-01-01", periods=40, freq="1D", tz="UTC", name="time")
    df = pd.DataFrame({"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0}, index=idx)
    df.loc[idx[30], ["open", "high", "low", "close"]] = [80.0, 81.0, 79.0, 80.0]  # gap down
    t = pd.Series(1.0, index=idx)
    res = run_backtest(df, t, "1d", FREE, RiskConfig(stop_atr_mult=2, max_drawdown_pct=0, daily_loss_limit_pct=0,
                                                       risk_per_trade_pct=100, max_position_pct=100, cooldown_hours=0))
    stops = [tr for tr in res.trades if tr.exit_reason == "stop"]
    assert stops and stops[0].exit_price == pytest.approx(80.0)


def test_kill_switch_flattens_and_stays_out():
    idx = pd.date_range("2024-01-01", periods=60, freq="1D", tz="UTC", name="time")
    px = [100.0] * 20 + [100 - 3 * i for i in range(1, 21)] + [40.0] * 20
    df = pd.DataFrame({"open": px, "high": px, "low": px, "close": px, "volume": 1.0}, index=idx)
    t = pd.Series(1.0, index=idx)
    res = run_backtest(df, t, "1d", FREE, RiskConfig(stop_atr_mult=0, max_drawdown_pct=20, daily_loss_limit_pct=0))
    assert res.halted
    assert res.exposure.iloc[-10:].max() == 0


def test_walk_forward_runs_out_of_sample_only(daily):
    wf = walk_forward(get_strategy("donchian", "1d"), daily, CostModel(), LOOSE, train_days=365, test_days=120)
    assert wf.folds and wf.oos.equity.index[0] >= daily.index[0] + pd.Timedelta(days=365)
