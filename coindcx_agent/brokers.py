"""Order execution: paper (simulated against the live order book) and live (CoinDCX)."""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass

from .config import AgentConfig
from .exchange import CoinDCXClient, CoinDCXError, MarketRules
from .state import Fill, StateStore

log = logging.getLogger(__name__)


@dataclass
class Holdings:
    cash: float   # quote currency available to the bot
    qty: float    # asset quantity owned *by the bot*
    bid: float
    ask: float

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2

    @property
    def equity(self) -> float:
        return self.cash + self.qty * self.bid  # mark at bid: what we'd really get

    @property
    def exposure(self) -> float:
        return self.qty * self.bid / self.equity if self.equity > 0 else 0.0


class Broker:
    mode = "base"

    def __init__(self, cfg: AgentConfig, client: CoinDCXClient, rules: MarketRules, store: StateStore):
        self.cfg, self.client, self.rules, self.store = cfg, client, rules, store
        self.inr = rules.quote == "INR"

    def holdings(self) -> Holdings:
        raise NotImplementedError

    def buy(self, value: float, reason: str, maker: bool = False) -> Fill | None:
        """Buy `value` of quote currency. maker=True rests a limit at the bid instead
        of crossing the spread; it may not fill (returns None)."""
        raise NotImplementedError

    def sell(self, qty: float, reason: str) -> Fill | None:
        raise NotImplementedError

    def _cap_value(self, value: float) -> float:
        cap = self.cfg.risk.max_order_value
        if cap > 0 and value > cap:
            log.warning("Order value %.2f capped to MAX_ORDER_VALUE %.2f", value, cap)
            return cap
        return value


class PaperBroker(Broker):
    """Fills instantly at the live best bid/ask plus slippage, charging fee + GST."""

    mode = "paper"

    def _key(self) -> str:
        return f"paper:{self.rules.symbol}"

    def _book(self) -> dict:
        return self.store.get(self._key()) or {"cash": self.cfg.trading.paper_starting_cash, "qty": 0.0}

    def holdings(self) -> Holdings:
        b = self._book()
        bid, ask = self.client.best_bid_ask(self.rules.pair)
        return Holdings(cash=b["cash"], qty=b["qty"], bid=bid, ask=ask)

    def buy(self, value, reason, maker=False):
        h = self.holdings()
        fee_rate = self.cfg.costs.effective_maker_fee if maker else self.cfg.costs.effective_fee
        value = min(self._cap_value(value), h.cash / (1 + fee_rate))
        if maker:
            px = self.rules.round_price(h.bid)
            if not self._wait_for_touch(px):
                log.info("Paper maker buy at %.4f not filled within %ss", px, self.cfg.trading.maker_wait_s)
                return None
        else:
            px = self.rules.round_price(h.ask * (1 + self.cfg.costs.slippage_pct / 100))
        qty = self.rules.round_qty(value / px)
        if err := self.rules.validate(qty, px):
            log.info("Paper buy skipped: %s", err)
            return None
        fee = qty * px * fee_rate
        b = self._book()
        b["cash"] -= qty * px + fee
        b["qty"] += qty
        return self._record(b, "buy", qty, px, fee, 0.0, reason)

    def _wait_for_touch(self, limit: float) -> bool:
        """Simulate a resting bid: filled once the best ask trades down to it."""
        deadline = time.time() + self.cfg.trading.maker_wait_s
        while time.time() < deadline:
            _, ask = self.client.best_bid_ask(self.rules.pair)
            if ask <= limit:
                return True
            time.sleep(2)
        return False

    def sell(self, qty, reason):
        h = self.holdings()
        qty = self.rules.round_qty(min(qty, h.qty))
        px = self.rules.round_price(h.bid * (1 - self.cfg.costs.slippage_pct / 100))
        selling_all = qty >= h.qty - self.rules.step
        if qty <= 0 or (not selling_all and (err := self.rules.validate(qty, px))):
            log.info("Paper sell skipped: %s", "nothing to sell" if qty <= 0 else err)
            return None
        value = qty * px
        fee = value * self.cfg.costs.effective_fee
        tds = value * self.cfg.costs.tds_pct / 100 if self.inr else 0.0
        b = self._book()
        b["cash"] += value - fee  # TDS is creditable; tracked, not deducted from paper cash
        b["qty"] = max(0.0, b["qty"] - qty)
        return self._record(b, "sell", qty, px, fee, tds, reason)

    def _record(self, book, side, qty, px, fee, tds, reason) -> Fill:
        f = Fill(time.time(), self.rules.symbol, side, qty, px, fee, tds, f"paper-{uuid.uuid4().hex[:10]}",
                 self.mode, reason)
        self.store.set(self._key(), book)
        self.store.add_fill(f)
        log.info("PAPER %s %.8f %s @ %.4f (fee %.2f) — %s", side.upper(), qty, self.rules.symbol, px, fee, reason)
        return f


class LiveBroker(Broker):
    """Real orders on CoinDCX.

    - Uses marketable limit orders at the best bid/ask (price-protected; no blind market orders).
    - Waits for the fill, cancels any unfilled remainder after `order_timeout_s`.
    - Tracks the quantity *the bot* bought, and never sells more than that, so coins
      you already held before starting the bot are never touched.
    - `capital_limit` caps how much of the quote balance the bot may use.
    """

    mode = "live"

    def _key(self) -> str:
        return f"live:{self.rules.symbol}:bot_qty"

    def bot_qty(self) -> float:
        return float(self.store.get(self._key(), 0.0))

    def holdings(self) -> Holdings:
        bal = self.client.balances()
        quote_free = bal.get(self.rules.quote, {}).get("free", 0.0)
        asset = bal.get(self.rules.asset, {})
        asset_total = asset.get("free", 0.0) + asset.get("locked", 0.0)
        qty = min(self.bot_qty(), asset_total)
        if qty < self.bot_qty() - self.rules.step:
            log.warning("Exchange shows %.8f %s but bot recorded %.8f; using exchange figure",
                        asset_total, self.rules.asset, self.bot_qty())
            self.store.set(self._key(), qty)
        bid, ask = self.client.best_bid_ask(self.rules.pair)
        limit = self.cfg.trading.capital_limit
        cash = quote_free
        if limit > 0:
            cash = max(0.0, min(quote_free, limit - qty * bid))
        return Holdings(cash=cash, qty=qty, bid=bid, ask=ask)

    def _execute(self, side: str, qty: float, price: float, reason: str, wait_s: int | None = None) -> Fill | None:
        cid = f"bot-{uuid.uuid4().hex[:16]}"
        try:
            order = self.client.create_order(self.rules.symbol, side, qty, price, "limit_order", cid)
        except (CoinDCXError, OSError) as e:
            # The request may have reached the exchange; look it up before giving up.
            log.error("Create order failed (%s); checking by client id", e)
            try:
                order = self.client.order_status(client_order_id=cid)
            except CoinDCXError:
                self.store.event("error", f"{side} {qty} failed: {e}")
                return None
        oid = order.get("id")
        deadline = time.time() + (wait_s or self.cfg.trading.order_timeout_s)
        status = order
        while time.time() < deadline:
            status = self.client.order_status(order_id=oid)
            if status.get("status") in ("filled", "cancelled", "rejected", "partially_cancelled"):
                break
            time.sleep(2)
        if status.get("status") not in ("filled", "cancelled", "rejected", "partially_cancelled"):
            try:
                self.client.cancel_order(oid)
            except CoinDCXError as e:
                log.warning("Cancel %s failed: %s", oid, e)
            time.sleep(1)
            status = self.client.order_status(order_id=oid)

        total = float(status.get("total_quantity") or qty)
        filled = total - float(status.get("remaining_quantity") or 0)
        if filled <= 0:
            log.warning("Order %s not filled (status %s)", oid, status.get("status"))
            self.store.event("warn", f"{side} order {oid} unfilled: {status.get('status')}")
            return None
        avg = float(status.get("avg_price") or price)
        fee = float(status.get("fee_amount") or filled * avg * self.cfg.costs.effective_fee)
        tds = filled * avg * self.cfg.costs.tds_pct / 100 if (self.inr and side == "sell") else 0.0
        new_qty = self.bot_qty() + filled if side == "buy" else max(0.0, self.bot_qty() - filled)
        self.store.set(self._key(), new_qty)
        f = Fill(time.time(), self.rules.symbol, side, filled, avg, fee, tds, str(oid), self.mode, reason)
        self.store.add_fill(f)
        log.info("LIVE %s %.8f %s @ %.4f (fee %.4f) — %s", side.upper(), filled, self.rules.symbol, avg, fee, reason)
        return f

    def buy(self, value, reason, maker=False):
        h = self.holdings()
        value = min(self._cap_value(value), h.cash / (1 + self.cfg.costs.effective_fee))
        px = self.rules.round_price(h.bid if maker else h.ask)
        qty = self.rules.round_qty(value / px)
        if err := self.rules.validate(qty, px):
            log.info("Live buy skipped: %s", err)
            return None
        return self._execute("buy", qty, px, reason, self.cfg.trading.maker_wait_s if maker else None)

    def sell(self, qty, reason):
        h = self.holdings()
        qty = self.rules.round_qty(min(qty, h.qty))
        if qty * h.bid > self.cfg.risk.max_order_value > 0 and reason not in ("kill_switch", "stop"):
            qty = self.rules.round_qty(self.cfg.risk.max_order_value / h.bid)
        px = self.rules.round_price(h.bid)
        if err := self.rules.validate(qty, px):
            log.info("Live sell skipped: %s", err)
            return None
        return self._execute("sell", qty, px, reason)
