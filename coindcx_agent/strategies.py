"""Long-only spot strategies.

Each strategy maps closed OHLCV candles to a *target exposure* series in [0, 1]:
0 = hold cash, 1 = fully long (before risk sizing). Spot markets can't be shorted,
so "sell" here only ever means "exit".

The same `target()` is used by the backtester and the live engine, so what you
backtest is what you trade. Lookbacks are given in days and converted to bars
for the candle interval, so one parameter set works on 15m, 1h and 1d candles.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from typing import ClassVar

import numpy as np
import pandas as pd

from . import indicators as ind
from .config import INTERVAL_SECONDS


def to_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Resample intraday candles to UTC daily candles, dropping an incomplete last day."""
    d = df.resample("1D").agg({"open": "first", "high": "max", "low": "min",
                               "close": "last", "volume": "sum"}).dropna()
    if len(df) and df.index[-1] + (df.index[1] - df.index[0] if len(df) > 1 else pd.Timedelta(0)) \
            < d.index[-1] + pd.Timedelta(days=1):
        d = d.iloc[:-1]
    return d


def _latch(entry: pd.Series, exit_: pd.Series) -> pd.Series:
    """1 from an entry bar until the next exit bar (stateful signal, vectorized)."""
    s = pd.Series(np.nan, index=entry.index)
    s[exit_.fillna(False).astype(bool)] = 0.0
    s[entry.fillna(False).astype(bool)] = 1.0  # entry wins if both fire on one bar
    return s.ffill().fillna(0.0)


@dataclass
class Strategy:
    name: ClassVar[str] = "base"
    kind: ClassVar[str] = ""
    description: ClassVar[str] = ""
    interval: str = "1h"
    # Decide on completed daily candles even when trading a shorter interval. Multi-day
    # signals evaluated every hour whipsaw around their thresholds and bleed fees.
    daily_signals: bool = True

    @property
    def bpd(self) -> float:
        """Bars per day."""
        return 86400 / INTERVAL_SECONDS[self.interval]

    # Defaults applied by the CLI unless overridden: preferred candle interval and
    # risk settings that define the strategy's holding horizon.
    default_interval: ClassVar[str] = "1h"
    risk_defaults: ClassVar[dict] = {}

    def hbars(self, hours: float) -> int:
        """Hours -> bars for this interval."""
        return max(1, int(round(hours * self.bpd / 24)))

    def bars(self, days: float) -> int:
        return max(2, int(round(days * self.bpd)))

    def _target(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

    def _daily_view(self) -> bool:
        return self.daily_signals and self.interval != "1d"

    def target(self, df: pd.DataFrame) -> pd.Series:
        """Target exposure for every bar of `df`, using only information available at its close."""
        if not self._daily_view():
            return self._target(df)
        daily = to_daily(df)
        t = replace(self, interval="1d", daily_signals=False)._target(daily)
        # A daily candle labelled D closes at D+1 00:00 UTC; only then is its signal known.
        t.index = t.index + pd.Timedelta(days=1)
        bar = pd.Timedelta(seconds=INTERVAL_SECONDS[self.interval])
        # The intraday bar that *closes* at D+1 00:00 opens at D+1 00:00 - bar.
        t.index = t.index - bar
        return t.reindex(df.index, method="ffill").fillna(0.0)

    def snapshot_for(self, df: pd.DataFrame) -> dict:
        if self._daily_view():
            return replace(self, interval="1d", daily_signals=False).snapshot(to_daily(df))
        return self.snapshot(df)

    def snapshot(self, df: pd.DataFrame) -> dict:
        """Latest indicator values, for display."""
        return {}

    def params(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self) if f.name not in ("interval", "daily_signals")}

    def with_params(self, **kw) -> "Strategy":
        return replace(self, **kw)

    @classmethod
    def param_grid(cls) -> dict[str, list]:
        """Small search space used by walk-forward optimisation."""
        return {}


@dataclass
class TrendVol(Strategy):
    """Multi-horizon time-series momentum with volatility targeting.

    Long when the average sign of returns over several lookbacks is positive and price
    is above its long EMA. Exposure is scaled so the position runs at roughly
    `target_vol` annualised volatility: smaller in wild markets, larger in calm ones.
    """

    name: ClassVar[str] = "trend_vol"
    kind: ClassVar[str] = "trend"
    description: ClassVar[str] = "Multi-horizon momentum + volatility targeting"
    lookbacks_days: tuple = (10, 30, 90)
    ema_days: float = 50
    vol_days: float = 20
    target_vol: float = 0.5

    band: float = 0.02   # hysteresis around the EMA: enter above +band, exit below -band
    step: float = 0.25   # exposure moves in steps, so it doesn't rebalance every bar

    def _target(self, df):
        c = df["close"]
        votes = sum(np.sign(c / c.shift(self.bars(d)) - 1) for d in self.lookbacks_days)
        score = (votes / len(self.lookbacks_days)).clip(lower=0)
        e = ind.ema(c, self.bars(self.ema_days))
        trend_ok = _latch(c > e * (1 + self.band), c < e * (1 - self.band))
        vol = ind.realized_vol(c, self.bars(self.vol_days), self.bpd * 365)
        scale = (self.target_vol / vol).clip(upper=1.0)
        raw = (score * scale * trend_ok).fillna(0.0).clip(0, 1)
        return (np.floor(raw / self.step + 1e-9) * self.step).clip(0, 1)

    def snapshot(self, df):
        c = df["close"]
        out = {f"ret_{d}d": float(c.iloc[-1] / c.iloc[-1 - self.bars(d)] - 1) for d in self.lookbacks_days
               if len(c) > self.bars(d)}
        out["ema"] = float(ind.ema(c, self.bars(self.ema_days)).iloc[-1])
        out["ann_vol"] = float(ind.realized_vol(c, self.bars(self.vol_days), self.bpd * 365).iloc[-1])
        return out

    @classmethod
    def param_grid(cls):
        return {"lookbacks_days": [(5, 20, 60), (10, 30, 90), (20, 60, 120)],
                "target_vol": [0.4, 0.6]}


@dataclass
class Donchian(Strategy):
    """Channel breakout (turtle-style): buy a new N-day high, exit at an M-day low."""

    name: ClassVar[str] = "donchian"
    kind: ClassVar[str] = "trend"
    description: ClassVar[str] = "Buy N-day high breakout, exit at M-day low"
    entry_days: float = 20
    exit_days: float = 10

    def _target(self, df):
        hi, _ = ind.donchian(df, self.bars(self.entry_days))
        _, lo = ind.donchian(df, self.bars(self.exit_days))
        return _latch(df["close"] > hi, df["close"] < lo)

    def snapshot(self, df):
        hi, _ = ind.donchian(df, self.bars(self.entry_days))
        _, lo = ind.donchian(df, self.bars(self.exit_days))
        return {"breakout_level": float(hi.iloc[-1]), "exit_level": float(lo.iloc[-1])}

    @classmethod
    def param_grid(cls):
        return {"entry_days": [10, 20, 40, 55], "exit_days": [5, 10, 20]}


@dataclass
class EMACross(Strategy):
    """Fast/slow EMA trend filter, only while the trend has strength (ADX)."""

    name: ClassVar[str] = "ema_cross"
    kind: ClassVar[str] = "trend"
    description: ClassVar[str] = "Fast EMA above slow EMA, with ADX trend-strength filter"
    fast_days: float = 10
    slow_days: float = 40
    adx_min: float = 15

    def _target(self, df):
        c = df["close"]
        fast, slow = ind.ema(c, self.bars(self.fast_days)), ind.ema(c, self.bars(self.slow_days))
        strong = ind.adx(df, max(14, self.bars(self.fast_days) // 2)) > self.adx_min
        return _latch((fast > slow) & strong, fast < slow)

    def snapshot(self, df):
        c = df["close"]
        return {"ema_fast": float(ind.ema(c, self.bars(self.fast_days)).iloc[-1]),
                "ema_slow": float(ind.ema(c, self.bars(self.slow_days)).iloc[-1]),
                "adx": float(ind.adx(df, max(14, self.bars(self.fast_days) // 2)).iloc[-1])}

    @classmethod
    def param_grid(cls):
        return {"fast_days": [5, 10, 20], "slow_days": [30, 50, 100]}


@dataclass
class MACDTrend(Strategy):
    """MACD above its signal line *and* above zero."""

    name: ClassVar[str] = "macd"
    kind: ClassVar[str] = "momentum"
    description: ClassVar[str] = "MACD above signal and above zero"
    fast_days: float = 12
    slow_days: float = 26
    signal_days: float = 9

    def _m(self, df):
        return ind.macd(df["close"], self.bars(self.fast_days), self.bars(self.slow_days),
                        self.bars(self.signal_days))

    def _target(self, df):
        line, sig, _ = self._m(df)
        return ((line > sig) & (line > 0)).astype(float)

    def snapshot(self, df):
        line, sig, hist = self._m(df)
        return {"macd": float(line.iloc[-1]), "signal": float(sig.iloc[-1]), "hist": float(hist.iloc[-1])}

    @classmethod
    def param_grid(cls):
        return {"fast_days": [6, 12], "slow_days": [26, 52], "signal_days": [9]}


@dataclass
class RSIDip(Strategy):
    """Buy oversold dips, but only inside a long-term uptrend; exit on recovery."""

    name: ClassVar[str] = "rsi_dip"
    kind: ClassVar[str] = "mean_reversion"
    description: ClassVar[str] = "Buy RSI dips while above long EMA, exit when RSI recovers"
    rsi_bars: int = 14
    entry_rsi: float = 30
    exit_rsi: float = 55
    trend_days: float = 100

    def _target(self, df):
        c = df["close"]
        r = ind.rsi(c, self.rsi_bars)
        uptrend = c > ind.ema(c, self.bars(self.trend_days))
        return _latch((r < self.entry_rsi) & uptrend, (r > self.exit_rsi) | ~uptrend)

    def snapshot(self, df):
        c = df["close"]
        return {"rsi": float(ind.rsi(c, self.rsi_bars).iloc[-1]),
                "trend_ema": float(ind.ema(c, self.bars(self.trend_days)).iloc[-1])}

    @classmethod
    def param_grid(cls):
        return {"entry_rsi": [20, 25, 30], "exit_rsi": [50, 60, 70]}


@dataclass
class BollingerRevert(Strategy):
    """Buy a close below the lower band in a non-downtrend, exit at the middle band."""

    name: ClassVar[str] = "bollinger"
    kind: ClassVar[str] = "mean_reversion"
    description: ClassVar[str] = "Buy below lower band (not in downtrend), exit at mid band"
    days: float = 5
    k: float = 2.0
    trend_days: float = 100

    def _target(self, df):
        c = df["close"]
        up, mid, lo = ind.bollinger(c, self.bars(self.days), self.k)
        ok = c > ind.ema(c, self.bars(self.trend_days)) * 0.95
        return _latch((c < lo) & ok, (c > mid) | ~ok)

    def snapshot(self, df):
        up, mid, lo = ind.bollinger(df["close"], self.bars(self.days), self.k)
        return {"upper": float(up.iloc[-1]), "mid": float(mid.iloc[-1]), "lower": float(lo.iloc[-1])}

    @classmethod
    def param_grid(cls):
        return {"days": [2, 5, 10], "k": [2.0, 2.5]}


@dataclass
class Ensemble(Strategy):
    """Average of the trend strategies' targets. Diversifies across signal types
    instead of requiring them all to agree on one bar (which rarely happens)."""

    name: ClassVar[str] = "ensemble"
    kind: ClassVar[str] = "ensemble"
    description: ClassVar[str] = "Average of trend_vol, donchian, ema_cross"
    members: tuple = ("trend_vol", "donchian", "ema_cross")

    def _members(self):
        return [STRATEGIES[m](interval=self.interval, daily_signals=False) for m in self.members]

    def _target(self, df):
        ts = [s._target(df) for s in self._members()]
        return (sum(ts) / len(ts)).clip(0, 1)

    def snapshot(self, df):
        return {s.name: round(float(s.target(df).iloc[-1]), 3) for s in self._members()}


# ── Intraday: 30 minute – 3 hour holding horizon ──────────────────
#
# These run on 15m candles and decide on every closed bar. Exits come from the
# strategy signal, a bar-ATR stop, a take-profit, and a hard 3h time exit (see
# INTRADAY_RISK). Only realistic on tight-spread markets (USDT pairs) with low fees.

INTRADAY_RISK = {
    "stop_atr_source": "bar", "stop_atr_mult": 2.0, "take_profit_atr_mult": 3.0,
    "min_hold_hours": 0.5, "max_hold_hours": 3.0, "cooldown_hours": 1.0,
    "trailing_stop": False, "risk_per_trade_pct": 1.0, "max_position_pct": 100.0,
    "rebalance_threshold": 0.5,
}


@dataclass
class IntradayStrategy(Strategy):
    kind: ClassVar[str] = "intraday"
    default_interval: ClassVar[str] = "15m"
    risk_defaults: ClassVar[dict] = INTRADAY_RISK
    interval: str = "15m"
    daily_signals: bool = False
    trend_hours: float = 24  # only trade long when price is above this EMA


@dataclass
class Breakout(IntradayStrategy):
    """Range breakout with volume confirmation, in the direction of the 1-day trend."""

    name: ClassVar[str] = "breakout"
    description: ClassVar[str] = "Close above the last N hours' high on above-average volume"
    range_hours: float = 4
    vol_mult: float = 1.5
    exit_ema_hours: float = 1

    def _target(self, df):
        c, v = df["close"], df["volume"]
        hi, _ = ind.donchian(df, self.hbars(self.range_hours))
        vol_ok = v > self.vol_mult * v.rolling(self.hbars(24)).mean().shift(1)
        trend = c > ind.ema(c, self.hbars(self.trend_hours))
        exit_ = c < ind.ema(c, self.hbars(self.exit_ema_hours) + 1)
        return _latch((c > hi) & vol_ok & trend, exit_)

    def snapshot(self, df):
        hi, _ = ind.donchian(df, self.hbars(self.range_hours))
        v = df["volume"]
        return {"range_high": float(hi.iloc[-1]),
                "volume_vs_avg": float(v.iloc[-1] / v.rolling(self.hbars(24)).mean().iloc[-2])}

    @classmethod
    def param_grid(cls):
        return {"range_hours": [2, 4, 8], "vol_mult": [1.2, 2.0]}


@dataclass
class RSI2Revert(IntradayStrategy):
    """Short-term pullback: buy a deeply oversold 2-bar RSI inside an uptrend, exit on the bounce."""

    name: ClassVar[str] = "rsi2"
    description: ClassVar[str] = "Buy RSI(2) < entry in an uptrend, exit when RSI(2) > exit"
    entry_rsi: float = 10
    exit_rsi: float = 70

    def _target(self, df):
        c = df["close"]
        r = ind.rsi(c, 2)
        trend = c > ind.ema(c, self.hbars(self.trend_hours))
        return _latch((r < self.entry_rsi) & trend, r > self.exit_rsi)

    def snapshot(self, df):
        return {"rsi2": float(ind.rsi(df["close"], 2).iloc[-1])}

    @classmethod
    def param_grid(cls):
        return {"entry_rsi": [5, 10, 20], "exit_rsi": [60, 80]}


@dataclass
class VWAPRevert(IntradayStrategy):
    """Buy a stretch below the rolling VWAP, exit back at VWAP."""

    name: ClassVar[str] = "vwap_revert"
    description: ClassVar[str] = "Buy when price is k std-devs below the rolling VWAP, exit at VWAP"
    vwap_hours: float = 24
    k: float = 2.0

    def _bands(self, df):
        n = self.hbars(self.vwap_hours)
        vw = ind.vwap_rolling(df, n)
        dev = (df["close"] - vw).rolling(n).std()
        return vw, dev

    def _target(self, df):
        c = df["close"]
        vw, dev = self._bands(df)
        trend = c > ind.ema(c, self.hbars(self.trend_hours * 3))
        return _latch((c < vw - self.k * dev) & trend, c > vw)

    def snapshot(self, df):
        vw, dev = self._bands(df)
        return {"vwap": float(vw.iloc[-1]), "z": float((df["close"].iloc[-1] - vw.iloc[-1]) / dev.iloc[-1])}

    @classmethod
    def param_grid(cls):
        return {"k": [1.5, 2.0, 2.5], "vwap_hours": [12, 24]}


@dataclass
class Squeeze(IntradayStrategy):
    """Volatility squeeze: after Bollinger bands are unusually narrow, buy the upside break."""

    name: ClassVar[str] = "squeeze"
    description: ClassVar[str] = "Buy a close above the upper band after a low-volatility squeeze"
    bb_bars: int = 20
    squeeze_pct: float = 0.2   # bandwidth in the lowest 20% of the last N days
    lookback_days: float = 5

    def _target(self, df):
        c = df["close"]
        up, mid, lo = ind.bollinger(c, self.bb_bars, 2.0)
        width = (up - lo) / mid
        thresh = width.rolling(self.bars(self.lookback_days)).quantile(self.squeeze_pct)
        was_tight = (width <= thresh).rolling(self.hbars(2)).max().shift(1).astype(bool)
        trend = c > ind.ema(c, self.hbars(self.trend_hours))
        return _latch((c > up) & was_tight & trend, c < mid)

    def snapshot(self, df):
        up, mid, lo = ind.bollinger(df["close"], self.bb_bars, 2.0)
        return {"upper": float(up.iloc[-1]), "bandwidth_pct": float(((up - lo) / mid).iloc[-1] * 100)}

    @classmethod
    def param_grid(cls):
        return {"squeeze_pct": [0.1, 0.2, 0.3], "bb_bars": [20, 40]}


STRATEGIES: dict[str, type[Strategy]] = {
    s.name: s for s in (TrendVol, Donchian, EMACross, MACDTrend, RSIDip, BollingerRevert, Ensemble,
                        Breakout, RSI2Revert, VWAPRevert, Squeeze)
}


def get_strategy(name: str, interval: str | None = None, **params) -> Strategy:
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy '{name}'. Available: {', '.join(STRATEGIES)}")
    cls = STRATEGIES[name]
    return cls(interval=interval or cls.default_interval, **params)


def apply_risk_defaults(strategy: Strategy, risk_cfg, explicit: set[str] = frozenset()) -> None:
    """Apply a strategy's horizon/risk profile to `risk_cfg`, except fields set explicitly."""
    for k, v in strategy.risk_defaults.items():
        if k not in explicit:
            setattr(risk_cfg, k, v)
