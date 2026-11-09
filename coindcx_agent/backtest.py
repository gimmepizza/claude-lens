"""Bar-by-bar backtester and walk-forward optimiser.

Honesty rules baked in:
- A signal computed on bar t's close is filled at bar t+1's open (no lookahead).
- Every fill pays half the spread + slippage + exchange fee + GST on the fee.
- Stops are checked against the bar's low; a gap through the stop fills at the open.
- Indian tax view: 1% TDS on INR sale value (reported, creditable) and 30%+cess on
  each profitable sale with no set-off for losses and no deduction for fees.
"""

from __future__ import annotations

import itertools
import logging
import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import indicators as ind
from .config import INTERVAL_SECONDS, CostModel, RiskConfig
from .risk import RiskManager
from .strategies import Strategy

log = logging.getLogger(__name__)


@dataclass
class Trade:
    entry_time: pd.Timestamp
    entry_price: float
    exit_time: pd.Timestamp | None = None
    exit_price: float = 0.0
    qty_max: float = 0.0
    cost: float = 0.0       # total cash paid in (incl. fees)
    proceeds: float = 0.0   # total cash received (after fees)
    exit_reason: str = ""

    @property
    def pnl(self) -> float:
        return self.proceeds - self.cost

    @property
    def ret(self) -> float:
        return self.pnl / self.cost if self.cost else 0.0


@dataclass
class BacktestResult:
    equity: pd.Series
    exposure: pd.Series
    trades: list[Trade]
    fees: float
    tds: float
    tax: float
    benchmark: pd.Series
    interval: str
    halted: str = ""
    metrics: dict = field(default_factory=dict)

    def trades_frame(self) -> pd.DataFrame:
        return pd.DataFrame([{**t.__dict__, "pnl": t.pnl, "ret": t.ret} for t in self.trades])


def _metrics(equity: pd.Series, interval: str) -> dict:
    if len(equity) < 2:
        return {}
    bars_per_year = 365 * 86400 / INTERVAL_SECONDS[interval]
    r = equity.pct_change().dropna()
    years = max((equity.index[-1] - equity.index[0]).total_seconds() / (365 * 86400), 1e-9)
    total = equity.iloc[-1] / equity.iloc[0] - 1
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1 if equity.iloc[-1] > 0 else -1.0
    vol = r.std() * math.sqrt(bars_per_year)
    downside = r[r < 0].std() * math.sqrt(bars_per_year)
    dd = equity / equity.cummax() - 1
    max_dd = dd.min()
    return {
        "total_return": total,
        "cagr": cagr,
        "ann_vol": vol,
        "sharpe": (r.mean() * bars_per_year) / vol if vol > 0 else 0.0,
        "sortino": (r.mean() * bars_per_year) / downside if downside > 0 else 0.0,
        "max_drawdown": max_dd,
        "calmar": cagr / abs(max_dd) if max_dd < 0 else 0.0,
    }


def run_backtest(
    df: pd.DataFrame,
    target: pd.Series,
    interval: str,
    costs: CostModel,
    risk_cfg: RiskConfig,
    starting_cash: float = 100000.0,
    min_notional: float = 0.0,
    inr_market: bool = True,
) -> BacktestResult:
    """Simulate trading `target` (exposure in [0, 1] per bar) over candles `df`."""
    df = df.loc[target.index.intersection(df.index)]
    target = target.reindex(df.index).fillna(0.0)
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    a = (ind.atr(df, risk_cfg.atr_bars) if risk_cfg.stop_atr_source == "bar"
         else ind.daily_atr(df, risk_cfg.atr_days)).to_numpy(float)
    tgt = target.to_numpy(float)
    idx = df.index
    n = len(df)

    fee_rate = costs.effective_fee
    maker_fee = costs.effective_maker_fee
    impact = costs.spread_pct / 200 + costs.slippage_pct / 100  # half spread + slippage
    tds_rate = costs.tds_pct / 100 if inr_market else 0.0
    tax_rate = costs.tax_rate_pct / 100

    rm = RiskManager(risk_cfg, bar_seconds=INTERVAL_SECONDS[interval])
    cash, qty, avg_cost = starting_cash, 0.0, 0.0
    fees = tds = taxable_gains = 0.0
    trades: list[Trade] = []
    open_trade: Trade | None = None
    pending: float | None = None  # desired equity fraction, decided at previous close
    pending_reason = "signal"
    maker_limit = 0.0             # resting maker buy price for this bar (0 = none)
    missed_entries = 0
    equity = np.empty(n)
    expo = np.empty(n)

    def buy(value: float, px_mid: float, t: pd.Timestamp, maker: bool = False):
        nonlocal cash, qty, avg_cost, fees, open_trade
        px = px_mid if maker else px_mid * (1 + impact)
        rate = maker_fee if maker else fee_rate
        fee = value * rate
        if value + fee > cash:
            value = cash / (1 + rate)
            fee = value * rate
        if value <= 0 or value < min_notional:
            return
        q = value / px
        avg_cost = (avg_cost * qty + px * q) / (qty + q)
        qty += q
        cash -= value + fee
        fees += fee
        if open_trade is None:
            open_trade = Trade(entry_time=t, entry_price=px)
        open_trade.cost += value + fee
        open_trade.qty_max = max(open_trade.qty_max, qty)

    def sell(q: float, px_mid: float, t: pd.Timestamp, reason: str, maker: bool = False):
        nonlocal cash, qty, fees, tds, taxable_gains, open_trade, avg_cost
        q = min(q, qty)
        px = px_mid if maker else px_mid * (1 - impact)
        value = q * px
        if q <= 0 or (value < min_notional and q < qty):
            return
        fee = value * (maker_fee if maker else fee_rate)
        cash += value - fee
        fees += fee
        tds += value * tds_rate
        taxable_gains += max(0.0, (px - avg_cost) * q)  # per-sale gains; losses not set off
        qty -= q
        if open_trade is not None:
            open_trade.proceeds += value - fee
            if qty <= 1e-12:
                qty = 0.0
                avg_cost = 0.0
                open_trade.exit_time, open_trade.exit_price, open_trade.exit_reason = t, px, reason
                trades.append(open_trade)
                open_trade = None

    for i in range(n):
        t = idx[i]
        prev_atr = a[i - 1] if i > 0 and not np.isnan(a[i - 1]) else 0.0
        # 1) fill the order decided at the previous close
        if pending is not None:
            eq_open = cash + qty * o[i]
            cur_val = qty * o[i]
            want_val = pending * eq_open
            was_flat = qty <= 0
            if pending <= 1e-9 and qty > 0:
                reason = "kill_switch" if rm.s.halted else pending_reason
                sell(qty, o[i], t, reason)
                rm.on_exit(reason=reason)
            elif want_val > cur_val:
                if was_flat and maker_limit > 0:
                    # resting bid: fills only if the market trades through it this bar
                    if l[i] < maker_limit:
                        buy(want_val - cur_val, min(o[i], maker_limit), t, maker=True)
                    else:
                        missed_entries += 1
                else:
                    buy(want_val - cur_val, o[i], t)
                if was_flat and qty > 0:
                    entry_px = open_trade.entry_price if open_trade else o[i]
                    rm.on_entry(entry_px, prev_atr)
            elif want_val < cur_val and qty > 0:
                sell((cur_val - want_val) / o[i], o[i], t, "rebalance")
            pending, pending_reason, maker_limit = None, "signal", 0.0

        # 2) protective stop, then take-profit, intrabar (stop first: conservative)
        if qty > 0 and rm.stop_triggered(l[i]):
            sell(qty, min(o[i], rm.s.stop_price), t, "stop")
            rm.on_exit(reason="stop")
        elif qty > 0 and rm.take_profit_triggered(h[i]):
            tp = rm.s.take_profit
            if costs.maker_entries:  # resting limit sell at the TP price
                sell(qty, max(o[i], tp), t, "take_profit", maker=True)
            else:
                sell(qty, max(o[i], tp), t, "take_profit")
            rm.on_exit(reason="take_profit")

        # 3) bar close bookkeeping
        eq = cash + qty * c[i]
        equity[i] = eq
        expo[i] = qty * c[i] / eq if eq > 0 else 0.0
        rm.update_equity(eq, t.to_pydatetime())
        if qty > 0:
            rm.on_bar(h[i], a[i])
        rm.tick()

        # 4) decide next bar's position
        if i == n - 1:
            break
        if qty > 0 and rm.time_exit_due():
            pending, pending_reason = 0.0, "time"
            continue
        atr_ok = not np.isnan(a[i])
        if atr_ok or not rm.uses_stop:
            want = rm.desired_fraction(tgt[i], c[i], a[i] if atr_ok else 0.0, expo[i])
            if abs(want - expo[i]) > 1e-6:
                pending = want
                if costs.maker_entries and expo[i] <= 1e-9 and want > 0:
                    maker_limit = c[i]  # join the bid at the signal bar's close

    # Close any open trade on paper so trade stats are complete (equity already marks it).
    if open_trade is not None:
        open_trade.exit_time, open_trade.exit_price, open_trade.exit_reason = idx[-1], c[-1], "open"
        open_trade.proceeds += qty * c[-1] * (1 - impact) * (1 - fee_rate)
        trades.append(open_trade)

    eq_s = pd.Series(equity, index=idx, name="equity")
    bench_qty = starting_cash / (1 + fee_rate) / (o[0] * (1 + impact))
    bench = pd.Series(bench_qty * c, index=idx, name="buy_and_hold")
    tax = taxable_gains * tax_rate

    res = BacktestResult(equity=eq_s, exposure=pd.Series(expo, index=idx), trades=trades, fees=fees,
                         tds=tds, tax=tax, benchmark=bench, interval=interval, halted=rm.s.halted)
    m = _metrics(eq_s, interval)
    closed = [t for t in trades if t.exit_reason != "open"]
    wins = [t.pnl for t in closed if t.pnl > 0]
    losses = [t.pnl for t in closed if t.pnl <= 0]
    m.update({
        "final_equity": float(eq_s.iloc[-1]),
        "after_tax_equity": float(eq_s.iloc[-1] - tax),
        "after_tax_return": float((eq_s.iloc[-1] - tax) / starting_cash - 1),
        "trades": len(trades),
        "win_rate": len(wins) / len(closed) if closed else 0.0,
        "profit_factor": sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else float("inf") if wins else 0.0,
        "avg_trade_ret": float(np.mean([t.ret for t in closed])) if closed else 0.0,
        "stops_hit": sum(1 for t in trades if t.exit_reason == "stop"),
        "exit_reasons": dict(pd.Series([t.exit_reason for t in trades]).value_counts()) if trades else {},
        "avg_hold_hours": float(np.mean([(t.exit_time - t.entry_time).total_seconds() / 3600
                                         for t in closed])) if closed else 0.0,
        "missed_maker_entries": missed_entries,
        "exposure": float(np.mean(expo)),
        "fees": fees,
        "fees_pct_of_start": fees / starting_cash,
        "tds_withheld": tds,
        "est_tax": tax,
    })
    bm = _metrics(bench, interval)
    m.update({f"bh_{k}": v for k, v in bm.items()})
    res.metrics = m
    return res


def backtest_strategy(strategy: Strategy, df: pd.DataFrame, costs: CostModel, risk_cfg: RiskConfig,
                      **kw) -> BacktestResult:
    return run_backtest(df, strategy.target(df), strategy.interval, costs, risk_cfg, **kw)


# ── walk-forward ──────────────────────────────────────────────────


def _score(m: dict) -> float:
    """Objective for picking parameters: risk-adjusted, penalising tiny samples."""
    if not m or m.get("trades", 0) < 3:
        return -1e9
    return m["sharpe"] + 0.5 * m["calmar"]


@dataclass
class WalkForwardResult:
    oos: BacktestResult
    folds: list[dict]


def walk_forward(strategy: Strategy, df: pd.DataFrame, costs: CostModel, risk_cfg: RiskConfig,
                 train_days: int = 365, test_days: int = 90, **kw) -> WalkForwardResult:
    """Re-optimise parameters on each rolling train window, trade them on the next
    unseen test window, and stitch only the out-of-sample periods together."""
    grid = strategy.param_grid()
    combos = [dict(zip(grid, v)) for v in itertools.product(*grid.values())] if grid else [{}]
    start, end = df.index[0], df.index[-1]
    fold_start = start + pd.Timedelta(days=train_days)
    oos_target = pd.Series(np.nan, index=df.index)
    folds = []

    while fold_start < end:
        fold_end = min(fold_start + pd.Timedelta(days=test_days), end)
        train = df[(df.index >= fold_start - pd.Timedelta(days=train_days)) & (df.index < fold_start)]
        best, best_score = combos[0], -np.inf
        for p in combos:
            s = strategy.with_params(**p)
            sc = _score(backtest_strategy(s, train, costs, risk_cfg, **kw).metrics)
            if sc > best_score:
                best, best_score = p, sc
        chosen = strategy.with_params(**best)
        # Compute on history up to fold_end so indicators are warm, then keep the test slice.
        hist = df[df.index < fold_end]
        t = chosen.target(hist)
        mask = (t.index >= fold_start) & (t.index < fold_end)
        oos_target.loc[t.index[mask]] = t[mask]
        folds.append({"test_start": fold_start.date(), "test_end": fold_end.date(),
                      "params": best, "train_score": round(best_score, 2)})
        fold_start = fold_end

    oos_target = oos_target.dropna()
    oos = run_backtest(df, oos_target, strategy.interval, costs, risk_cfg, **kw)
    return WalkForwardResult(oos=oos, folds=folds)
