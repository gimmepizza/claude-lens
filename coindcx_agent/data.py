"""Historical and live candle data, with a local CSV cache."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import pandas as pd

from .config import INTERVAL_SECONDS
from .exchange import CoinDCXClient

log = logging.getLogger(__name__)

COLUMNS = ["time", "open", "high", "low", "close", "volume"]


def to_frame(raw: list[dict]) -> pd.DataFrame:
    """Convert CoinDCX candle dicts to a clean, time-indexed, ascending DataFrame."""
    if not raw:
        return pd.DataFrame(columns=COLUMNS[1:], index=pd.DatetimeIndex([], name="time", tz="UTC"))
    df = pd.DataFrame(raw)[COLUMNS]  # select by name: never rely on dict key order
    df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
    for c in COLUMNS[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna().drop_duplicates("time").sort_values("time").set_index("time")
    return df


def drop_forming_candle(df: pd.DataFrame, interval: str, now: float | None = None) -> pd.DataFrame:
    """Remove the last candle if it has not closed yet.

    Strategies must only see closed candles; the still-forming one changes every
    second and makes signals flicker (and makes backtests lie).
    """
    if df.empty:
        return df
    now = time.time() if now is None else now
    last_open = df.index[-1].timestamp()
    if last_open + INTERVAL_SECONDS[interval] > now:
        return df.iloc[:-1]
    return df


class CandleStore:
    def __init__(self, client: CoinDCXClient, data_dir: str = "data"):
        self.client = client
        self.dir = Path(data_dir)

    def _path(self, pair: str, interval: str) -> Path:
        return self.dir / f"{pair.replace('-', '_')}_{interval}.csv"

    def _fetch_range(self, pair: str, interval: str, start_ms: int, end_ms: int) -> list[pd.DataFrame]:
        step = INTERVAL_SECONDS[interval] * 1000
        frames, cursor = [], start_ms
        while cursor < end_ms:
            chunk_end = min(cursor + 1000 * step, end_ms)
            raw = self.client.candles(pair, interval, 1000, cursor, chunk_end)
            if raw:
                frames.append(to_frame(raw))
            cursor = chunk_end + 1
        return frames

    def latest(self, pair: str, interval: str, n: int = 400) -> pd.DataFrame:
        """Last `n` closed candles, straight from the API (for live trading)."""
        now_ms = int(time.time() * 1000)
        start_ms = now_ms - (n + 2) * INTERVAL_SECONDS[interval] * 1000
        frames = self._fetch_range(pair, interval, start_ms, now_ms)
        if not frames:
            return to_frame([])
        df = pd.concat(frames).sort_index()
        df = df[~df.index.duplicated(keep="last")]
        return drop_forming_candle(df, interval).tail(n)

    def history(self, pair: str, interval: str, days: int, refresh: bool = True) -> pd.DataFrame:
        """Up to `days` of closed candles, cached to CSV and topped up incrementally."""
        path = self._path(pair, interval)
        cached = pd.read_csv(path, index_col="time", parse_dates=["time"]) if path.exists() else None
        if cached is not None and cached.index.tz is None:
            cached.index = cached.index.tz_localize("UTC")

        now_ms = int(time.time() * 1000)
        want_start = now_ms - days * 86400 * 1000
        step = INTERVAL_SECONDS[interval] * 1000
        frames = [cached] if cached is not None and not cached.empty else []

        ranges: list[tuple[int, int]] = []
        if cached is None or cached.empty:
            ranges.append((want_start, now_ms))
        else:
            first = int(cached.index[0].timestamp() * 1000)
            last = int(cached.index[-1].timestamp() * 1000)
            if want_start < first - step:
                ranges.append((want_start, first - 1))
            if refresh and now_ms > last + 2 * step:
                ranges.append((last + 1, now_ms))

        for start, end in ranges:
            frames.extend(self._fetch_range(pair, interval, start, end))

        if not frames:
            return to_frame([])
        df = pd.concat(frames).sort_index()
        df = df[~df.index.duplicated(keep="last")]
        df = drop_forming_candle(df, interval)
        self.dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(path)
        return df[df.index >= pd.to_datetime(want_start, unit="ms", utc=True)]
