"""Command line interface.  Run `python -m coindcx_agent --help`."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

from tabulate import tabulate

from . import __version__
from .backtest import backtest_strategy, walk_forward
from .config import AgentConfig
from .data import CandleStore
from .exchange import CoinDCXClient
from .strategies import STRATEGIES, apply_risk_defaults, get_strategy

log = logging.getLogger("coindcx_agent")

LIVE_CONFIRM_ENV = "LIVE_TRADING_CONFIRM"
LIVE_CONFIRM_VALUE = "I_ACCEPT_THE_RISK"


def _pct(x):
    return f"{x:.1%}" if isinstance(x, (int, float)) else str(x)


def _num(x, nd=2):
    return f"{x:,.{nd}f}" if isinstance(x, (int, float)) else str(x)


# risk field -> (CLI flag attr, env var). A value set either way beats a strategy's defaults.
RISK_OVERRIDES = {
    "stop_atr_mult": ("stop", "STOP_ATR_MULT"), "max_position_pct": ("max_position", "MAX_POSITION_PCT"),
    "risk_per_trade_pct": ("risk_per_trade", "RISK_PER_TRADE_PCT"), "max_drawdown_pct": ("max_dd", "MAX_DRAWDOWN_PCT"),
    "take_profit_atr_mult": ("take_profit", "TAKE_PROFIT_ATR_MULT"), "min_hold_hours": ("min_hold", "MIN_HOLD_HOURS"),
    "max_hold_hours": ("max_hold", "MAX_HOLD_HOURS"), "stop_atr_source": ("stop_source", "STOP_ATR_SOURCE"),
    "max_order_value": ("max_order_value", "MAX_ORDER_VALUE"),
}


def build_config(a, strategy_name: str | None = None) -> AgentConfig:
    cfg = AgentConfig()
    t, r, c = cfg.trading, cfg.risk, cfg.costs
    t.market = getattr(a, "market", None) or t.market
    t.strategy = strategy_name or getattr(a, "strategy", None) or t.strategy
    cls = STRATEGIES.get(t.strategy)
    t.interval = getattr(a, "interval", None) or t.interval or (cls.default_interval if cls else "1h")
    explicit = set()
    for field, (attr, env) in RISK_OVERRIDES.items():
        v = getattr(a, attr, None)
        if v is not None:
            setattr(r, field, v)
        if v is not None or os.getenv(env):
            explicit.add(field)
    if cls:
        apply_risk_defaults(cls(interval=t.interval), r, explicit)
    for attr, obj, field in [("fee", c, "fee_pct"), ("spread", c, "spread_pct"), ("slippage", c, "slippage_pct"),
                             ("maker_fee", c, "maker_fee_pct"), ("capital_limit", t, "capital_limit"),
                             ("poll", t, "poll_s"), ("state_db", t, "state_db")]:
        v = getattr(a, attr, None)
        if v is not None:
            setattr(obj, field, v)
    if getattr(a, "maker", False):
        c.maker_entries = True
    return cfg


def _strategy(a, cfg):
    params = json.loads(a.params) if getattr(a, "params", None) else {}
    s = get_strategy(cfg.trading.strategy, cfg.trading.interval, **params)
    if getattr(a, "intraday_signals", False):
        s = s.with_params(daily_signals=False)
    return s


def _history(client, cfg, rules, days):
    return CandleStore(client, cfg.data_dir).history(rules.pair, cfg.trading.interval, days)


def _bt_kwargs(rules):
    return {"min_notional": rules.min_notional, "inr_market": rules.quote == "INR"}


def _costs_for(cfg, rules, a):
    """USDT markets: no TDS; tighter default spread unless overridden."""
    if rules.quote != "INR":
        cfg.costs.tds_pct = 0.0
        if getattr(a, "spread", None) is None:
            cfg.costs.spread_pct = 0.05
    return cfg.costs


# ── market info ───────────────────────────────────────────────────


def cmd_markets(a, cfg, client):
    rules = client.all_rules()
    q = (a.search or "").upper()
    tick = {t["market"]: t for t in client.ticker()}
    rows = []
    for sym, r in sorted(rules.items()):
        if q and q not in sym:
            continue
        t = tick.get(sym, {})
        rows.append([sym, r.pair, r.quote, t.get("last_price", ""), _num(float(t.get("volume") or 0), 0),
                     f"{float(t.get('change_24_hour') or 0):+.2f}%", r.min_notional])
    rows.sort(key=lambda x: -float(str(x[4]).replace(",", "") or 0))
    print(tabulate(rows[: a.limit], headers=["market", "pair", "quote", "last", "24h vol", "24h", "min order"]))


def cmd_ticker(a, cfg, client):
    rules = client.rules(cfg.trading.market)
    t = client.ticker_for(rules.symbol) or {}
    bid, ask = client.best_bid_ask(rules.pair)
    print(tabulate([[k, v] for k, v in t.items()], tablefmt="plain"))
    print(f"\norder book: bid {bid:,.4f} | ask {ask:,.4f} | spread {(ask - bid) / ask:.3%}")


def cmd_book(a, cfg, client):
    rules = client.rules(cfg.trading.market)
    book = client.orderbook(rules.pair)
    bids = sorted(((float(p), float(q)) for p, q in book.get("bids", {}).items()), reverse=True)[: a.depth]
    asks = sorted((float(p), float(q)) for p, q in book.get("asks", {}).items())[: a.depth]
    rows = [[f"{b[1]:.6f}", f"{b[0]:,.4f}", f"{s[0]:,.4f}", f"{s[1]:.6f}"] for b, s in zip(bids, asks)]
    print(tabulate(rows, headers=["bid qty", "bid", "ask", "ask qty"]))
    if bids and asks:
        print(f"\nspread {(asks[0][0] - bids[0][0]) / asks[0][0]:.3%}")


def cmd_balance(a, cfg, client):
    bal = client.balances()
    rows = [[k, v["free"], v["locked"]] for k, v in sorted(bal.items()) if v["free"] or v["locked"]]
    print(tabulate(rows, headers=["currency", "free", "locked"]))


def cmd_fetch(a, cfg, client):
    rules = client.rules(cfg.trading.market)
    df = _history(client, cfg, rules, a.days)
    print(f"{rules.symbol} {cfg.trading.interval}: {len(df)} candles, {df.index[0]} → {df.index[-1]} "
          f"(cached in {cfg.data_dir}/)")


# ── research ──────────────────────────────────────────────────────


def _print_metrics(m, title):
    rows = [
        ["Total return", _pct(m["total_return"]), _pct(m["bh_total_return"])],
        ["After est. tax", _pct(m["after_tax_return"]), "(taxed only when sold)"],
        ["CAGR", _pct(m["cagr"]), _pct(m["bh_cagr"])],
        ["Sharpe", _num(m["sharpe"]), _num(m["bh_sharpe"])],
        ["Sortino", _num(m["sortino"]), _num(m["bh_sortino"])],
        ["Max drawdown", _pct(m["max_drawdown"]), _pct(m["bh_max_drawdown"])],
        ["Calmar", _num(m["calmar"]), _num(m["bh_calmar"])],
        ["Time in market", _pct(m["exposure"]), "100%"],
        ["Round trips", m["trades"], 1],
        ["Win rate", _pct(m["win_rate"]), ""],
        ["Profit factor", _num(m["profit_factor"]), ""],
        ["Avg trade / avg hold", f"{m['avg_trade_ret']:+.2%} / {m['avg_hold_hours']:.1f}h", ""],
        ["Exits", ", ".join(f"{k} {v}" for k, v in m["exit_reasons"].items()), ""],
        ["Fees + GST paid", _num(m["fees"]), ""],
        ["TDS withheld (creditable)", _num(m["tds_withheld"]), ""],
        ["Est. tax on gains", _num(m["est_tax"]), ""],
    ]
    print(f"\n{title}\n")
    print(tabulate(rows, headers=["", "strategy", "buy & hold"]))


def cmd_backtest(a, cfg, client):
    rules = client.rules(cfg.trading.market)
    costs = _costs_for(cfg, rules, a)
    df = _history(client, cfg, rules, a.days)
    s = _strategy(a, cfg)
    res = backtest_strategy(s, df, costs, cfg.risk, starting_cash=a.cash, **_bt_kwargs(rules))
    _print_metrics(res.metrics, f"{s.name} on {rules.symbol} {cfg.trading.interval} | {df.index[0].date()} → "
                                f"{df.index[-1].date()} | fee {costs.fee_pct}%+GST, spread {costs.spread_pct}%, "
                                f"slippage {costs.slippage_pct}% | params {s.params()}")
    if res.halted:
        print(f"\n⚠ Kill switch would have fired: {res.halted}")
    if a.trades:
        tf = res.trades_frame()
        if not tf.empty:
            print()
            print(tabulate(tf[["entry_time", "exit_time", "entry_price", "exit_price", "pnl", "ret", "exit_reason"]]
                           .tail(a.trades), headers="keys", showindex=False, floatfmt=",.2f"))
    if a.out:
        res.equity.to_frame().join(res.benchmark).join(res.exposure.rename("exposure")).to_csv(a.out)
        print(f"\nequity curve written to {a.out}")
    if a.report:
        from .report import write_report
        write_report(a.report, res, s, rules.symbol, cfg)
        print(f"HTML report written to {a.report}")


def cmd_compare(a, cfg, client):
    rules = client.rules(cfg.trading.market)
    intraday = cfg.trading.interval in ("1m", "15m")
    names = [n for n, c in STRATEGIES.items() if (c.kind == "intraday") == intraday]
    df = _history(client, cfg, rules, a.days)
    rows, m = [], {}
    for name in names:
        scfg = build_config(a, strategy_name=name)  # each strategy with its own horizon profile
        costs = _costs_for(scfg, rules, a)
        s = get_strategy(name, cfg.trading.interval)
        res = backtest_strategy(s, df, costs, scfg.risk, **_bt_kwargs(rules))
        m = res.metrics
        row = [name, _pct(m["total_return"]), _pct(m["after_tax_return"]), _num(m["sharpe"]),
               _pct(m["max_drawdown"]), m["trades"], f"{m['avg_trade_ret']:+.2%}", f"{m['avg_hold_hours']:.1f}h",
               res.halted.split(" at ")[-1][:10] if res.halted else ""]
        if a.walk_forward and STRATEGIES[name].param_grid():
            w = walk_forward(s, df, costs, scfg.risk, a.train_days, a.test_days, **_bt_kwargs(rules)).oos.metrics
            row += [_pct(w["total_return"]), _num(w["sharpe"]), _pct(w["bh_total_return"])]
        rows.append(row)
    rows.append(["buy & hold", _pct(m["bh_total_return"]), "", _num(m["bh_sharpe"]),
                 _pct(m["bh_max_drawdown"]), 1, "", "", ""])
    headers = ["strategy", "return", "after tax", "sharpe", "max DD", "trades", "avg trade", "avg hold", "kill switch"]
    if a.walk_forward:
        headers += ["OOS return", "OOS sharpe", "B&H same span"]
    costs = _costs_for(cfg, rules, a)
    print(f"\n{rules.symbol} {cfg.trading.interval} {df.index[0].date()} → {df.index[-1].date()} "
          f"(fee {costs.fee_pct}%+GST{', maker entries ' + str(costs.maker_fee_pct) + '%' if costs.maker_entries else ''}"
          f", spread {costs.spread_pct}%)\n")
    print(tabulate(rows, headers=headers))
    if a.walk_forward:
        print("\nOOS = walk-forward out-of-sample: parameters re-chosen on the previous "
              f"{a.train_days} days, then traded on the next {a.test_days} unseen days.")


def cmd_walkforward(a, cfg, client):
    rules = client.rules(cfg.trading.market)
    costs = _costs_for(cfg, rules, a)
    df = _history(client, cfg, rules, a.days)
    s = _strategy(a, cfg)
    wf = walk_forward(s, df, costs, cfg.risk, a.train_days, a.test_days, starting_cash=a.cash, **_bt_kwargs(rules))
    print(tabulate([[f["test_start"], f["test_end"], f["params"], f["train_score"]] for f in wf.folds],
                   headers=["test from", "to", "chosen params", "train score"]))
    _print_metrics(wf.oos.metrics, f"Walk-forward OOS: {s.name} on {rules.symbol} {cfg.trading.interval}")


def cmd_signal(a, cfg, client):
    from .engine import Engine
    from .brokers import PaperBroker
    from .state import StateStore
    rules = client.rules(cfg.trading.market)
    eng = Engine(cfg, _strategy(a, cfg), PaperBroker(cfg, client, rules, StateStore(":memory:")), StateStore(":memory:"))
    sig = eng.compute_signal()
    print(f"\n{eng.strategy.name} on {rules.symbol} — last closed {eng.signal_interval} candle {sig['bar']}\n")
    print(f"  target exposure : {sig['target']:.0%}")
    print(f"  max size (risk) : {eng.rm.max_fraction(sig['close'], sig['atr']):.0%} of equity")
    print(f"  close / ATR     : {sig['close']:,.4f} / {sig['atr']:,.4f}")
    for k, v in sig["snapshot"].items():
        print(f"  {k:<16}: {_num(v, 4) if isinstance(v, float) else v}")


# ── trading ───────────────────────────────────────────────────────


def _engine(a, cfg, client, live: bool):
    from .brokers import LiveBroker, PaperBroker
    from .engine import Engine
    from .state import StateStore
    rules = client.rules(cfg.trading.market)
    _costs_for(cfg, rules, a)
    store = StateStore(cfg.trading.state_db)
    broker = (LiveBroker if live else PaperBroker)(cfg, client, rules, store)
    return Engine(cfg, _strategy(a, cfg), broker, store)


def cmd_paper(a, cfg, client):
    eng = _engine(a, cfg, client, live=False)
    print(f"PAPER trading {eng.rules.symbol} with {eng.strategy.name} (signals on {eng.signal_interval} candles). "
          f"State: {cfg.trading.state_db}. Ctrl+C to stop.")
    if a.once:
        print(json.dumps(eng.step(force_decision=True), indent=2, default=str))
    else:
        eng.run()


def cmd_live(a, cfg, client):
    if not cfg.api.has_credentials:
        sys.exit("Set COINDCX_API_KEY and COINDCX_API_SECRET in .env first.")
    if os.getenv(LIVE_CONFIRM_ENV) != LIVE_CONFIRM_VALUE:
        sys.exit(f"Live trading is locked. Set {LIVE_CONFIRM_ENV}={LIVE_CONFIRM_VALUE} in your environment "
                 "once you have paper-traded and accept that you can lose money.")
    eng = _engine(a, cfg, client, live=True)
    h = eng.broker.holdings()
    print(f"\nLIVE trading {eng.rules.symbol} with {eng.strategy.name}")
    print(f"  bot capital limit : {cfg.trading.capital_limit or 'entire free balance'} {eng.rules.quote}")
    print(f"  max order value   : {cfg.risk.max_order_value} {eng.rules.quote}")
    print(f"  usable cash now   : {h.cash:,.2f} {eng.rules.quote}; bot-owned {eng.rules.asset}: {h.qty}")
    print(f"  kill switch       : create a file named '{cfg.trading.kill_switch_file}' or drawdown ≥ "
          f"{cfg.risk.max_drawdown_pct}%")
    if not a.yes:
        if input(f"\nType the market name ({eng.rules.symbol}) to start: ").strip() != eng.rules.symbol:
            sys.exit("Aborted.")
    if a.once:
        print(json.dumps(eng.step(force_decision=True), indent=2, default=str))
    else:
        eng.run()


def cmd_status(a, cfg, client):
    from .state import StateStore
    store = StateStore(cfg.trading.state_db)
    sym = cfg.trading.market
    for mode in ("paper", "live"):
        risk = store.get(f"risk:{mode}:{sym}")
        if not risk:
            continue
        eq = store.equity_history(sym, mode, 100000)
        print(f"\n[{mode}] {sym}")
        if eq:
            first, last = eq[0][1], eq[-1][1]
            print(f"  equity {last:,.2f} (started {first:,.2f}, {last / first - 1:+.2%}) "
                  f"as of {datetime.fromtimestamp(eq[-1][0], timezone.utc):%Y-%m-%d %H:%M} UTC")
        print(f"  last decision bar: {store.get(f'risk:{mode}:{sym}:last_bar')}")
        print(f"  risk: {json.dumps(risk)}")
    fills = store.fills(sym, a.limit)
    if fills:
        print()
        print(tabulate([[datetime.fromtimestamp(f["ts"], timezone.utc).strftime("%m-%d %H:%M"), f["mode"], f["side"],
                         f["qty"], f["price"], round(f["fee"], 4), f["reason"]] for f in fills],
                       headers=["time (UTC)", "mode", "side", "qty", "price", "fee", "reason"]))
    ev = store.events(10)
    if ev:
        print()
        for ts, lvl, msg in ev:
            print(f"  {datetime.fromtimestamp(ts, timezone.utc):%m-%d %H:%M} {lvl:5} {msg}")


def cmd_reset_halt(a, cfg, client):
    from .state import StateStore
    store = StateStore(cfg.trading.state_db)
    key = f"risk:{a.mode}:{cfg.trading.market}"
    risk = store.get(key) or {}
    print(f"Clearing halt: {risk.get('halted') or '(none)'}; peak equity reset.")
    risk.update(halted="", peak_equity=0.0)
    store.set(key, risk)


# ── parser ────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="coindcx_agent", description=f"CoinDCX algo trading agent v{__version__}")
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp, strategy=False, costs=False):
        sp.add_argument("-m", "--market", help="e.g. BTCINR, ETHUSDT (default from .env)")
        sp.add_argument("-i", "--interval", choices=["1m", "15m", "1h", "1d"])
        if strategy:
            sp.add_argument("-s", "--strategy", choices=list(STRATEGIES))
            sp.add_argument("--params", help='JSON strategy params, e.g. \'{"entry_days": 40}\'')
            sp.add_argument("--intraday-signals", action="store_true",
                            help="evaluate signals on every bar instead of on daily closes (usually worse)")
            sp.add_argument("--stop", type=float, help="protective stop in daily ATRs (0 = off)")
            sp.add_argument("--max-position", type=float, help="max %% of equity in the asset")
            sp.add_argument("--risk-per-trade", type=float, help="%% of equity lost if the stop is hit")
            sp.add_argument("--max-dd", type=float, help="kill switch drawdown %% (0 = off)")
            sp.add_argument("--stop-source", choices=["daily", "bar"], help="ATR for stops: daily candles or trading bars")
            sp.add_argument("--take-profit", type=float, help="take profit in ATRs (0 = off)")
            sp.add_argument("--min-hold", type=float, help="minimum holding time in hours")
            sp.add_argument("--max-hold", type=float, help="maximum holding time in hours (time exit; 0 = off)")
            sp.add_argument("--max-order-value", type=float, help="cap on any single order")
        if costs:
            sp.add_argument("--fee", type=float, help="fee %% per fill before GST (default 0.5)")
            sp.add_argument("--spread", type=float, help="assumed bid/ask spread %%")
            sp.add_argument("--slippage", type=float, help="extra slippage %% per fill")
            sp.add_argument("--maker", action="store_true", help="enter with resting limit orders at the bid")
            sp.add_argument("--maker-fee", type=float, help="maker fee %% before GST")

    sp = sub.add_parser("markets", help="list markets by volume")
    sp.add_argument("--search")
    sp.add_argument("--limit", type=int, default=30)
    sp = sub.add_parser("ticker", help="price and spread for a market")
    common(sp)
    sp = sub.add_parser("book", help="order book")
    common(sp)
    sp.add_argument("--depth", type=int, default=10)
    sub.add_parser("balance", help="your CoinDCX balances (needs API keys)")
    sp = sub.add_parser("fetch", help="download candle history to the local cache")
    common(sp)
    sp.add_argument("--days", type=int, default=1100)

    for name, hlp in [("backtest", "backtest one strategy"), ("compare", "backtest every strategy"),
                      ("walkforward", "walk-forward (out-of-sample) test")]:
        sp = sub.add_parser(name, help=hlp)
        common(sp, strategy=True, costs=True)
        sp.add_argument("--days", type=int, default=1100)
        sp.add_argument("--cash", type=float, default=100000.0)
        if name == "backtest":
            sp.add_argument("--trades", type=int, default=0, help="show the last N trades")
            sp.add_argument("--out", help="write equity curve CSV")
            sp.add_argument("--report", help="write an HTML report")
        else:
            sp.add_argument("--train-days", type=int, default=365)
            sp.add_argument("--test-days", type=int, default=90)
        if name == "compare":
            sp.add_argument("--walk-forward", action="store_true")

    sp = sub.add_parser("signal", help="current signal for a market")
    common(sp, strategy=True)
    for name, hlp in [("paper", "paper trade against live prices"), ("live", "trade real money")]:
        sp = sub.add_parser(name, help=hlp)
        common(sp, strategy=True, costs=True)
        sp.add_argument("--once", action="store_true", help="run one cycle and exit")
        sp.add_argument("--poll", type=int, help="seconds between checks")
        sp.add_argument("--state-db")
        sp.add_argument("--capital-limit", type=float, help="max quote currency the bot may use (live)")
        if name == "live":
            sp.add_argument("--yes", action="store_true", help="skip the interactive confirmation")
    sp = sub.add_parser("status", help="positions, equity, fills and events from the state DB")
    common(sp)
    sp.add_argument("--state-db")
    sp.add_argument("--limit", type=int, default=15)
    sp = sub.add_parser("reset-halt", help="clear a kill-switch halt after you've reviewed it")
    common(sp)
    sp.add_argument("--mode", choices=["paper", "live"], default="paper")
    sp.add_argument("--state-db")
    return p


COMMANDS = {
    "markets": cmd_markets, "ticker": cmd_ticker, "book": cmd_book, "balance": cmd_balance,
    "fetch": cmd_fetch, "backtest": cmd_backtest, "compare": cmd_compare, "walkforward": cmd_walkforward,
    "signal": cmd_signal, "paper": cmd_paper, "live": cmd_live, "status": cmd_status,
    "reset-halt": cmd_reset_halt,
}


def main(argv=None):
    a = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    cfg = build_config(a)
    client = CoinDCXClient(cfg.api)
    try:
        COMMANDS[a.cmd](a, cfg, client)
    except (ValueError, RuntimeError) as e:
        sys.exit(f"error: {e}")
