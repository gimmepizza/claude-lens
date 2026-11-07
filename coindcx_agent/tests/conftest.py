import numpy as np
import pandas as pd
import pytest

from coindcx_agent.exchange import MarketRules

RULES_RAW = {
    "symbol": "BTCINR", "pair": "I-BTC_INR", "target_currency_short_name": "BTC",
    "base_currency_short_name": "INR", "base_currency_precision": 1, "target_currency_precision": 5,
    "step": 1e-05, "min_quantity": 1e-05, "max_quantity": 2, "max_quantity_market": 0.0158,
    "min_notional": 100, "order_types": ["limit_order", "market_order"], "status": "active",
}


@pytest.fixture
def rules():
    return MarketRules.from_api(RULES_RAW)


def make_candles(n=900, freq="1D", seed=1, drift=0.0005, vol=0.03, start="2023-01-01"):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, periods=n, freq=freq, tz="UTC", name="time")
    r = rng.normal(drift, vol, n)
    close = 100 * np.exp(np.cumsum(r))
    open_ = np.r_[100, close[:-1]]
    high = np.maximum(open_, close) * (1 + rng.uniform(0, vol / 2, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, vol / 2, n))
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close,
                         "volume": rng.uniform(1, 10, n)}, index=idx)


@pytest.fixture
def daily():
    return make_candles()
