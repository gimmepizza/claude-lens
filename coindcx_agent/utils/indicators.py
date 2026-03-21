"""Technical indicator calculations for quant trading strategies."""

import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def bollinger_bands(
    series: pd.Series, period: int = 20, std_dev: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Bollinger Bands: returns (upper, middle, lower)."""
    middle = sma(series, period)
    std = series.rolling(window=period).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return upper, middle, lower


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """MACD: returns (macd_line, signal_line, histogram)."""
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def vwap(df: pd.DataFrame) -> pd.Series:
    """Volume Weighted Average Price.

    Expects DataFrame with 'high', 'low', 'close', 'volume' columns.
    """
    typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
    cumulative_tp_vol = (typical_price * df["volume"]).cumsum()
    cumulative_vol = df["volume"].cumsum()
    return cumulative_tp_vol / cumulative_vol


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range.

    Expects DataFrame with 'high', 'low', 'close' columns.
    """
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)

    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)

    return tr.rolling(window=period).mean()


def stochastic_rsi(
    series: pd.Series, rsi_period: int = 14, stoch_period: int = 14
) -> pd.Series:
    """Stochastic RSI."""
    rsi_values = rsi(series, rsi_period)
    min_rsi = rsi_values.rolling(window=stoch_period).min()
    max_rsi = rsi_values.rolling(window=stoch_period).max()
    stoch = (rsi_values - min_rsi) / (max_rsi - min_rsi)
    return stoch * 100


def obv(df: pd.DataFrame) -> pd.Series:
    """On Balance Volume.

    Expects DataFrame with 'close' and 'volume' columns.
    """
    direction = np.sign(df["close"].diff())
    return (direction * df["volume"]).cumsum()
