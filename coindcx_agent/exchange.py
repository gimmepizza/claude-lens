"""CoinDCX REST client: signing, retries, rate limiting, and exchange order rules."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import threading
import time
from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal
from typing import Any

import requests

from .config import APIConfig

log = logging.getLogger(__name__)


class CoinDCXError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"CoinDCX API error {status}: {message}")


class _RateLimiter:
    def __init__(self, per_second: float):
        self.min_gap = 1.0 / per_second if per_second > 0 else 0.0
        self._last = 0.0
        self._lock = threading.Lock()

    def wait(self):
        with self._lock:
            gap = self._last + self.min_gap - time.monotonic()
            if gap > 0:
                time.sleep(gap)
            self._last = time.monotonic()


@dataclass(frozen=True)
class MarketRules:
    """Order rules for one market, from /exchange/v1/markets_details.

    CoinDCX's naming is inverted from the usual convention: for BTCINR,
    `target_currency` is BTC (what you buy) and `base_currency` is INR (what you pay).
    Here `asset` is BTC and `quote` is INR.
    """

    symbol: str
    pair: str
    asset: str
    quote: str
    price_precision: int
    qty_precision: int
    step: float
    min_qty: float
    max_qty: float
    max_qty_market: float
    min_notional: float
    order_types: tuple[str, ...]

    @classmethod
    def from_api(cls, m: dict) -> "MarketRules":
        return cls(
            symbol=m["symbol"],
            pair=m["pair"],
            asset=m["target_currency_short_name"],
            quote=m["base_currency_short_name"],
            price_precision=int(m.get("base_currency_precision") or 2),
            qty_precision=int(m.get("target_currency_precision") or 6),
            step=float(m.get("step") or 0) or 10 ** -int(m.get("target_currency_precision") or 6),
            min_qty=float(m.get("min_quantity") or 0),
            max_qty=float(m.get("max_quantity") or float("inf")),
            max_qty_market=float(m.get("max_quantity_market") or float("inf")),
            min_notional=float(m.get("min_notional") or 0),
            order_types=tuple(m.get("order_types") or ()),
        )

    def round_qty(self, qty: float) -> float:
        """Round quantity *down* to the market step (never order more than intended)."""
        step = Decimal(str(self.step))
        q = (Decimal(str(qty)) / step).to_integral_value(rounding=ROUND_DOWN) * step
        return float(q.quantize(Decimal(1).scaleb(-self.qty_precision), rounding=ROUND_DOWN))

    def round_price(self, price: float) -> float:
        return float(Decimal(str(price)).quantize(Decimal(1).scaleb(-self.price_precision)))

    def validate(self, qty: float, price: float, market_order: bool = False) -> str | None:
        """Return a reason the order would be rejected, or None if it is fine."""
        if qty <= 0:
            return "quantity rounds to zero"
        if qty < self.min_qty:
            return f"quantity {qty} below minimum {self.min_qty}"
        cap = self.max_qty_market if market_order else self.max_qty
        if qty > cap:
            return f"quantity {qty} above maximum {cap}"
        if qty * price < self.min_notional:
            return f"order value {qty * price:.2f} below minimum {self.min_notional} {self.quote}"
        return None


class CoinDCXClient:
    RETRY_STATUS = {429, 500, 502, 503, 504}

    def __init__(self, config: APIConfig | None = None):
        self.config = config or APIConfig()
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json", "User-Agent": "coindcx-agent/2"})
        self._limiter = _RateLimiter(self.config.max_requests_per_second)
        self._rules: dict[str, MarketRules] | None = None

    # ── transport ──────────────────────────────────────────────────

    def _request(self, method: str, url: str, **kw) -> Any:
        kw.setdefault("timeout", self.config.timeout)
        last_err: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            self._limiter.wait()
            try:
                resp = self.session.request(method, url, **kw)
            except (requests.ConnectionError, requests.Timeout) as e:
                last_err = e
                log.warning("%s %s failed (%s), retry %d", method, url, e, attempt + 1)
            else:
                if resp.status_code == 200:
                    return resp.json() if resp.text else {}
                if resp.status_code not in self.RETRY_STATUS:
                    raise CoinDCXError(resp.status_code, resp.text[:500])
                last_err = CoinDCXError(resp.status_code, resp.text[:500])
                log.warning("%s %s -> %d, retry %d", method, url, resp.status_code, attempt + 1)
            time.sleep(min(2 ** attempt, 16))
        raise last_err  # type: ignore[misc]

    def _get(self, url: str, params: dict | None = None) -> Any:
        return self._request("GET", url, params=params)

    def sign(self, body: dict) -> tuple[str, str]:
        payload = json.dumps(body, separators=(",", ":"))
        sig = hmac.new(self.config.api_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return payload, sig

    def _private(self, endpoint: str, body: dict | None = None) -> Any:
        if not self.config.has_credentials:
            raise CoinDCXError(0, "COINDCX_API_KEY / COINDCX_API_SECRET are not set")
        body = dict(body or {})
        body["timestamp"] = int(time.time() * 1000)
        payload, sig = self.sign(body)
        headers = {"X-AUTH-APIKEY": self.config.api_key, "X-AUTH-SIGNATURE": sig}
        # Order creation is not idempotent: never blind-retry it (a retry could double-fill).
        if endpoint.endswith("/orders/create"):
            self._limiter.wait()
            resp = self.session.post(self.config.base_url + endpoint, data=payload,
                                     headers=headers, timeout=self.config.timeout)
            if resp.status_code != 200:
                raise CoinDCXError(resp.status_code, resp.text[:500])
            return resp.json() if resp.text else {}
        return self._request("POST", self.config.base_url + endpoint, data=payload, headers=headers)

    # ── public ─────────────────────────────────────────────────────

    def ticker(self) -> list[dict]:
        return self._get(f"{self.config.base_url}/exchange/ticker")

    def ticker_for(self, symbol: str) -> dict | None:
        return next((t for t in self.ticker() if t.get("market") == symbol), None)

    def markets_details(self) -> list[dict]:
        return self._get(f"{self.config.base_url}/exchange/v1/markets_details")

    def all_rules(self) -> dict[str, MarketRules]:
        if self._rules is None:
            self._rules = {m["symbol"]: MarketRules.from_api(m) for m in self.markets_details()
                           if m.get("status") == "active"}
        return self._rules

    def rules(self, symbol: str) -> MarketRules:
        rules = self.all_rules()
        if symbol not in rules:
            raise ValueError(f"Unknown or inactive market '{symbol}'. Try: markets --search {symbol[:3]}")
        return rules[symbol]

    def orderbook(self, pair: str) -> dict:
        return self._get(f"{self.config.public_url}/market_data/orderbook", {"pair": pair})

    def best_bid_ask(self, pair: str) -> tuple[float, float]:
        book = self.orderbook(pair)
        bids = [float(p) for p in (book.get("bids") or {})]
        asks = [float(p) for p in (book.get("asks") or {})]
        if not bids or not asks:
            raise CoinDCXError(0, f"empty order book for {pair}")
        return max(bids), min(asks)

    def candles(self, pair: str, interval: str, limit: int = 1000,
                start_ms: int | None = None, end_ms: int | None = None) -> list[dict]:
        params: dict[str, Any] = {"pair": pair, "interval": interval, "limit": min(limit, 1000)}
        if start_ms is not None and end_ms is not None:
            params["startTime"], params["endTime"] = start_ms, end_ms
        return self._get(f"{self.config.public_url}/market_data/candles", params)

    def recent_trades(self, pair: str, limit: int = 50) -> list[dict]:
        return self._get(f"{self.config.public_url}/market_data/trade_history",
                         {"pair": pair, "limit": min(limit, 500)})

    # ── private ────────────────────────────────────────────────────

    def balances(self) -> dict[str, dict[str, float]]:
        out = {}
        for b in self._private("/exchange/v1/users/balances"):
            out[b["currency"]] = {"free": float(b.get("balance") or 0),
                                  "locked": float(b.get("locked_balance") or 0)}
        return out

    def create_order(self, symbol: str, side: str, qty: float, price: float | None = None,
                     order_type: str = "limit_order", client_order_id: str | None = None) -> dict:
        body: dict[str, Any] = {"market": symbol, "side": side, "order_type": order_type,
                                "total_quantity": qty}
        if price is not None and order_type != "market_order":
            body["price_per_unit"] = price
        if client_order_id:
            body["client_order_id"] = client_order_id
        resp = self._private("/exchange/v1/orders/create", body)
        orders = resp.get("orders") if isinstance(resp, dict) else None
        return orders[0] if orders else resp

    def order_status(self, order_id: str | None = None, client_order_id: str | None = None) -> dict:
        body = {"id": order_id} if order_id else {"client_order_id": client_order_id}
        return self._private("/exchange/v1/orders/status", body)

    def cancel_order(self, order_id: str) -> dict:
        return self._private("/exchange/v1/orders/cancel", {"id": order_id})

    def cancel_all(self, symbol: str) -> dict:
        return self._private("/exchange/v1/orders/cancel_all", {"market": symbol})

    def active_orders(self, symbol: str) -> list[dict]:
        resp = self._private("/exchange/v1/orders/active_orders", {"market": symbol})
        return resp.get("orders", []) if isinstance(resp, dict) else resp

    def trade_history(self, limit: int = 500) -> list[dict]:
        return self._private("/exchange/v1/orders/trade_history", {"limit": min(limit, 5000)})
