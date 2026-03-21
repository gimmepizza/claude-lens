"""Market data fetching and processing for quant analysis."""

import logging
from typing import Any

import numpy as np
import pandas as pd

from .api_client import CoinDCXClient


logger = logging.getLogger(__name__)


class MarketDataFetcher:
    """Fetches and processes market data from CoinDCX into DataFrames."""

    def __init__(self, client: CoinDCXClient):
        self.client = client
        self._market_details_cache: list[dict] | None = None

    def get_market_pair(self, market: str) -> str | None:
        """Resolve a market symbol (e.g., 'BTCINR') to the pair format used by
        public endpoints (e.g., 'I-BTC_INR').

        Returns None if the market is not found.
        """
        details = self.get_all_market_details()
        for m in details:
            if m.get("symbol") == market:
                return m.get("pair")
        return None

    def get_all_market_details(self) -> list[dict]:
        """Get and cache all market details."""
        if self._market_details_cache is None:
            self._market_details_cache = self.client.get_markets_details()
        return self._market_details_cache

    def get_market_info(self, market: str) -> dict | None:
        """Get details for a specific market."""
        details = self.get_all_market_details()
        for m in details:
            if m.get("symbol") == market:
                return m
        return None

    def get_candles_df(
        self,
        pair: str,
        interval: str = "5m",
        limit: int = 100,
    ) -> pd.DataFrame:
        """Fetch candle data and return as a DataFrame.

        Returns DataFrame with columns: time, open, high, low, close, volume
        """
        raw = self.client.get_candles(pair=pair, interval=interval, limit=limit)

        if not raw:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

        df = pd.DataFrame(raw)
        df.columns = ["time", "open", "high", "low", "close", "volume"]
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.sort_values("time").reset_index(drop=True)
        return df

    def get_ticker_for_market(self, market: str) -> dict | None:
        """Get current ticker data for a specific market."""
        tickers = self.client.get_ticker()
        for t in tickers:
            if t.get("market") == market:
                return t
        return None

    def get_orderbook_df(self, pair: str) -> dict[str, pd.DataFrame]:
        """Get order book as DataFrames for bids and asks."""
        book = self.client.get_orderbook(pair=pair)

        result = {}
        for side in ["bids", "asks"]:
            data = book.get(side, {})
            if data:
                rows = [{"price": float(p), "quantity": float(q)} for p, q in data.items()]
                result[side] = pd.DataFrame(rows).sort_values(
                    "price", ascending=(side == "asks")
                ).reset_index(drop=True)
            else:
                result[side] = pd.DataFrame(columns=["price", "quantity"])

        return result

    def get_recent_trades_df(self, pair: str, limit: int = 100) -> pd.DataFrame:
        """Get recent trades as a DataFrame."""
        raw = self.client.get_trades(pair=pair, limit=limit)

        if not raw:
            return pd.DataFrame(columns=["time", "price", "quantity", "symbol"])

        df = pd.DataFrame(raw)
        rename_map = {"T": "time", "p": "price", "q": "quantity", "s": "symbol"}
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"], unit="ms")
        for col in ["price", "quantity"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df.sort_values("time").reset_index(drop=True) if "time" in df.columns else df

    def get_spread(self, pair: str) -> dict[str, float]:
        """Calculate current bid-ask spread."""
        book = self.get_orderbook_df(pair)
        best_bid = book["bids"]["price"].iloc[0] if not book["bids"].empty else 0
        best_ask = book["asks"]["price"].iloc[0] if not book["asks"].empty else 0
        spread = best_ask - best_bid
        spread_pct = (spread / best_ask * 100) if best_ask > 0 else 0

        return {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "spread_pct": spread_pct,
        }
