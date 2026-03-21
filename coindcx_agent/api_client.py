"""CoinDCX REST API client with HMAC-SHA256 authentication."""

import hmac
import hashlib
import json
import time
import logging
from typing import Any

import requests

from .config import APIConfig


logger = logging.getLogger(__name__)


class CoinDCXAPIError(Exception):
    """Custom exception for CoinDCX API errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"CoinDCX API Error ({status_code}): {message}")


class CoinDCXClient:
    """CoinDCX REST API client.

    Handles authentication, request signing, and all API interactions
    for both public and private endpoints.
    """

    def __init__(self, config: APIConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _get_timestamp(self) -> int:
        return int(round(time.time() * 1000))

    def _sign(self, body: dict) -> tuple[str, str]:
        """Generate HMAC-SHA256 signature for request body."""
        json_body = json.dumps(body, separators=(",", ":"))
        signature = hmac.new(
            bytes(self.config.api_secret, "utf-8"),
            json_body.encode(),
            hashlib.sha256,
        ).hexdigest()
        return json_body, signature

    def _authenticated_headers(self, signature: str) -> dict:
        return {
            "Content-Type": "application/json",
            "X-AUTH-APIKEY": self.config.api_key,
            "X-AUTH-SIGNATURE": signature,
        }

    def _post_authenticated(self, endpoint: str, body: dict) -> Any:
        """Make an authenticated POST request."""
        body["timestamp"] = self._get_timestamp()
        json_body, signature = self._sign(body)
        headers = self._authenticated_headers(signature)
        url = f"{self.config.base_url}{endpoint}"

        logger.debug("POST %s", url)
        response = self.session.post(url, data=json_body, headers=headers)

        if response.status_code != 200:
            raise CoinDCXAPIError(response.status_code, response.text)

        if response.text:
            return response.json()
        return {}

    def _get_public(self, url: str, params: dict | None = None) -> Any:
        """Make a public GET request."""
        logger.debug("GET %s params=%s", url, params)
        response = self.session.get(url, params=params)

        if response.status_code != 200:
            raise CoinDCXAPIError(response.status_code, response.text)

        return response.json()

    # ── Public Market Data ──────────────────────────────────────────

    def get_ticker(self) -> list[dict]:
        """Get ticker data for all markets."""
        return self._get_public(f"{self.config.base_url}/exchange/ticker")

    def get_markets(self) -> list[str]:
        """Get list of active market symbols."""
        return self._get_public(f"{self.config.base_url}/exchange/v1/markets")

    def get_markets_details(self) -> list[dict]:
        """Get detailed market information including trading parameters."""
        return self._get_public(f"{self.config.base_url}/exchange/v1/markets_details")

    def get_orderbook(self, pair: str) -> dict:
        """Get order book for a trading pair.

        Args:
            pair: Trading pair symbol (e.g., 'B-BTC_USDT')
        """
        return self._get_public(
            f"{self.config.public_url}/market_data/orderbook",
            params={"pair": pair},
        )

    def get_candles(
        self,
        pair: str,
        interval: str = "5m",
        limit: int = 100,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> list:
        """Get OHLCV candle data.

        Args:
            pair: Trading pair symbol
            interval: Candle interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 1d, 3d, 1w, 1M)
            limit: Number of candles (default 100)
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
        """
        params = {"pair": pair, "interval": interval, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        return self._get_public(
            f"{self.config.public_url}/market_data/candles",
            params=params,
        )

    def get_trades(self, pair: str, limit: int = 30) -> list[dict]:
        """Get recent trade history for a pair.

        Args:
            pair: Trading pair symbol
            limit: Number of trades (max 500)
        """
        return self._get_public(
            f"{self.config.public_url}/market_data/trade_history",
            params={"pair": pair, "limit": min(limit, 500)},
        )

    # ── User / Account ──────────────────────────────────────────────

    def get_balances(self) -> list[dict]:
        """Get user wallet balances."""
        return self._post_authenticated("/exchange/v1/users/balances", {})

    def get_user_info(self) -> dict:
        """Get user account information."""
        return self._post_authenticated("/exchange/v1/users/info", {})

    # ── Order Management ────────────────────────────────────────────

    def create_order(
        self,
        market: str,
        side: str,
        order_type: str,
        total_quantity: float,
        price_per_unit: float | None = None,
        client_order_id: str | None = None,
    ) -> dict:
        """Place a new order.

        Args:
            market: Market symbol (e.g., 'BTCINR')
            side: 'buy' or 'sell'
            order_type: 'limit_order' or 'market_order'
            total_quantity: Quantity to trade
            price_per_unit: Price per unit (required for limit orders)
            client_order_id: Optional client-assigned order ID
        """
        body = {
            "market": market,
            "side": side,
            "order_type": order_type,
            "total_quantity": total_quantity,
        }
        if price_per_unit is not None:
            body["price_per_unit"] = price_per_unit
        if client_order_id:
            body["client_order_id"] = client_order_id

        return self._post_authenticated("/exchange/v1/orders/create", body)

    def cancel_order(self, order_id: str) -> dict:
        """Cancel a specific order by ID."""
        return self._post_authenticated(
            "/exchange/v1/orders/cancel", {"id": order_id}
        )

    def cancel_orders_by_ids(self, order_ids: list[str]) -> dict:
        """Cancel multiple orders by their IDs."""
        return self._post_authenticated(
            "/exchange/v1/orders/cancel_by_ids", {"ids": order_ids}
        )

    def cancel_all_orders(self, market: str, side: str | None = None) -> dict:
        """Cancel all orders for a market."""
        body = {"market": market}
        if side:
            body["side"] = side
        return self._post_authenticated("/exchange/v1/orders/cancel_all", body)

    def get_active_orders(self, market: str, side: str | None = None) -> list[dict]:
        """Get all active orders for a market."""
        body = {"market": market}
        if side:
            body["side"] = side
        return self._post_authenticated("/exchange/v1/orders/active_orders", body)

    def get_order_status(self, order_id: str) -> dict:
        """Get status of a specific order."""
        return self._post_authenticated(
            "/exchange/v1/orders/status", {"id": order_id}
        )

    def edit_order_price(self, order_id: str, new_price: float) -> dict:
        """Edit the price of an existing order."""
        return self._post_authenticated(
            "/exchange/v1/orders/edit",
            {"id": order_id, "price_per_unit": new_price},
        )

    def get_trade_history(
        self, limit: int = 500, sort: str = "desc", from_id: str | None = None
    ) -> list[dict]:
        """Get user's trade history."""
        body = {"limit": min(limit, 5000), "sort": sort}
        if from_id:
            body["from_id"] = from_id
        return self._post_authenticated("/exchange/v1/orders/trade_history", body)
