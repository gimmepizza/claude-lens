import hashlib
import hmac


from coindcx_agent.config import APIConfig
from coindcx_agent.data import drop_forming_candle, to_frame
from coindcx_agent.exchange import CoinDCXClient


def test_quote_and_asset_are_not_swapped(rules):
    # CoinDCX calls INR the "base" and BTC the "target"; the bot must spend INR.
    assert rules.asset == "BTC" and rules.quote == "INR"


def test_round_qty_never_rounds_up(rules):
    assert rules.round_qty(0.0123499) == 0.01234
    assert rules.round_qty(0.00000999) == 0.0


def test_round_price(rules):
    assert rules.round_price(7512345.678) == 7512345.7


def test_validate(rules):
    assert "below minimum 100" in rules.validate(0.00001, 7_500_000)
    assert rules.validate(0.001, 7_500_000) is None
    assert "above maximum" in rules.validate(0.02, 7_500_000, market_order=True)
    assert rules.validate(0, 1) == "quantity rounds to zero"


def test_signature_matches_coindcx_scheme():
    c = CoinDCXClient(APIConfig(api_key="k", api_secret="s"))
    body = {"market": "BTCINR", "timestamp": 1}
    payload, sig = c.sign(body)
    assert payload == '{"market":"BTCINR","timestamp":1}'
    assert sig == hmac.new(b"s", payload.encode(), hashlib.sha256).hexdigest()


def test_to_frame_selects_columns_by_name_not_order():
    raw = [{"time": 3600000, "volume": 5, "close": 4, "low": 1, "high": 9, "open": 2},
           {"close": 3, "open": 1, "high": 8, "low": 0.5, "volume": 1, "time": 0}]
    df = to_frame(raw)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert df.index.is_monotonic_increasing
    assert df.iloc[1].tolist() == [2, 9, 1, 4, 5]


def test_drop_forming_candle():
    df = to_frame([{"time": 0, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
                   {"time": 3_600_000, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}])
    assert len(drop_forming_candle(df, "1h", now=3_600 + 1800)) == 1   # 2nd still forming
    assert len(drop_forming_candle(df, "1h", now=7_200 + 1)) == 2      # both closed
