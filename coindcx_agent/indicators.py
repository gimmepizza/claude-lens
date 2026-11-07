"""Technical indicators. Every value at bar t uses only data up to and including bar t."""

from __future__ import annotations

import numpy as np
import pandas as pd


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    """Wilder's RSI."""
    d = s.diff()
    gain = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = gain / loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    return out.where(loss != 0, 100.0).where(gain.notna())


def true_range(df: pd.DataFrame) -> pd.Series:
    pc = df["close"].shift(1)
    return pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()],
                     axis=1).max(axis=1)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """Wilder's ATR."""
    return true_range(df).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def bollinger(s: pd.Series, n: int = 20, k: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series]:
    mid = sma(s, n)
    sd = s.rolling(n, min_periods=n).std()
    return mid + k * sd, mid, mid - k * sd


def macd(s: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    line = ema(s, fast) - ema(s, slow)
    sig = ema(line, signal)
    return line, sig, line - sig


def donchian(df: pd.DataFrame, n: int) -> tuple[pd.Series, pd.Series]:
    """Highest high / lowest low of the *previous* n bars (excludes the current bar)."""
    return df["high"].rolling(n).max().shift(1), df["low"].rolling(n).min().shift(1)


def adx(df: pd.DataFrame, n: int = 14) -> pd.Series:
    up = df["high"].diff()
    down = -df["low"].diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    tr = atr(df, n)
    plus_di = 100 * plus_dm.ewm(alpha=1 / n, adjust=False, min_periods=n).mean() / tr
    minus_di = 100 * minus_dm.ewm(alpha=1 / n, adjust=False, min_periods=n).mean() / tr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def realized_vol(s: pd.Series, n: int, bars_per_year: float) -> pd.Series:
    """Annualized volatility of log returns over n bars."""
    r = np.log(s).diff()
    return r.rolling(n, min_periods=n).std() * np.sqrt(bars_per_year)


def vwap_rolling(df: pd.DataFrame, n: int) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    return (tp * df["volume"]).rolling(n).sum() / df["volume"].rolling(n).sum()


def daily_atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """ATR of *daily* candles, aligned to the bars of `df`, using completed days only.

    Stops sized from intraday ATR sit inside normal intraday noise and get hit
    constantly; daily ATR matches the horizon the strategies actually trade.
    """
    d = df.resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    a = atr(d, n).shift(1)  # today's value only uses days that have closed
    return a.reindex(df.index, method="ffill")
