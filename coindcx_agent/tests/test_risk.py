from datetime import datetime, timedelta, timezone

from coindcx_agent.config import RiskConfig
from coindcx_agent.risk import RiskManager

T0 = datetime(2024, 1, 1, 6, tzinfo=timezone.utc)


def test_size_capped_by_stop_distance():
    rm = RiskManager(RiskConfig(stop_atr_mult=2, risk_per_trade_pct=1, max_position_pct=100))
    # stop distance 2*5/100 = 10% -> 1% risk allows 10% of equity
    assert abs(rm.max_fraction(100, 5) - 0.10) < 1e-9


def test_no_stop_means_max_position():
    assert RiskManager(RiskConfig(stop_atr_mult=0, max_position_pct=60)).max_fraction(100, 5) == 0.6


def test_trailing_stop_only_moves_up():
    rm = RiskManager(RiskConfig(stop_atr_mult=2))
    rm.on_entry(100, 5)
    assert rm.s.stop_price == 90
    rm.on_bar(high=120, atr=5)
    assert rm.s.stop_price == 110
    rm.on_bar(high=105, atr=5)
    assert rm.s.stop_price == 110
    assert rm.stop_triggered(109) and not rm.stop_triggered(111)


def test_cooldown_blocks_reentry():
    rm = RiskManager(RiskConfig(stop_atr_mult=2, cooldown_hours=48), bar_seconds=86400)
    rm.on_entry(100, 5)
    rm.on_exit(stopped=True)
    assert rm.desired_fraction(1, 100, 5, 0) == 0
    rm.tick(); rm.tick()
    assert rm.desired_fraction(1, 100, 5, 0) > 0


def test_daily_loss_blocks_adding_but_allows_reducing():
    rm = RiskManager(RiskConfig(stop_atr_mult=0, daily_loss_limit_pct=3, rebalance_threshold=0))
    rm.update_equity(100, T0)
    rm.update_equity(96, T0 + timedelta(hours=2))
    assert rm.s.day_halted
    assert rm.desired_fraction(1, 100, 5, 0.3) == 0.3
    assert rm.desired_fraction(0.1, 100, 5, 0.3) == 0.1
    rm.update_equity(96, T0 + timedelta(days=1))
    assert not rm.s.day_halted


def test_max_drawdown_halts():
    rm = RiskManager(RiskConfig(max_drawdown_pct=20))
    rm.update_equity(100, T0)
    rm.update_equity(79, T0 + timedelta(days=3))
    assert rm.s.halted and rm.desired_fraction(1, 100, 5, 0.5) == 0


def test_rebalance_threshold_avoids_churn():
    rm = RiskManager(RiskConfig(stop_atr_mult=0, rebalance_threshold=0.2))
    assert rm.desired_fraction(0.55, 100, 5, 0.5) == 0.5
    assert rm.desired_fraction(1.0, 100, 5, 0.5) == 1.0
