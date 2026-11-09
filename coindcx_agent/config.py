"""Configuration. Values come from defaults, then environment (.env), then CLI flags."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default):
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    if isinstance(default, bool):
        return raw.strip().lower() in ("1", "true", "yes", "y", "on")
    return type(default)(raw)


@dataclass
class APIConfig:
    api_key: str = field(default_factory=lambda: _env("COINDCX_API_KEY", ""))
    api_secret: str = field(default_factory=lambda: _env("COINDCX_API_SECRET", ""))
    base_url: str = "https://api.coindcx.com"
    public_url: str = "https://public.coindcx.com"
    timeout: float = 10.0
    max_retries: int = 4
    # CoinDCX does not publish a hard number for every endpoint; stay well under.
    max_requests_per_second: float = 8.0

    @property
    def has_credentials(self) -> bool:
        return bool(self.api_key and self.api_secret)


@dataclass
class CostModel:
    """Trading costs. Check your own fee tier on CoinDCX and adjust."""

    fee_pct: float = field(default_factory=lambda: _env("FEE_PCT", 0.5))
    # 18% GST is charged on the exchange fee itself.
    gst_on_fee_pct: float = field(default_factory=lambda: _env("GST_ON_FEE_PCT", 18.0))
    # Extra slippage on top of the half-spread, per fill.
    slippage_pct: float = field(default_factory=lambda: _env("SLIPPAGE_PCT", 0.05))
    # Used by the backtester when there is no live order book (candles have no bid/ask).
    spread_pct: float = field(default_factory=lambda: _env("SPREAD_PCT", 0.3))
    # India: 1% TDS withheld on the sale value of crypto (s.194S). Creditable, but it
    # ties up capital until you file. Only applies to INR markets.
    tds_pct: float = field(default_factory=lambda: _env("TDS_PCT", 1.0))
    # India: flat 30% + 4% cess on VDA gains; losses cannot be set off.
    tax_rate_pct: float = field(default_factory=lambda: _env("TAX_RATE_PCT", 31.2))
    # Entries as resting limit orders at the bid (maker) instead of crossing the spread.
    # A maker entry only fills if price trades down to it within `maker_wait_bars`.
    maker_entries: bool = field(default_factory=lambda: _env("MAKER_ENTRIES", False))
    maker_fee_pct: float = field(default_factory=lambda: _env("MAKER_FEE_PCT", 0.5))

    @property
    def effective_fee(self) -> float:
        """Taker fee per fill as a fraction, GST included."""
        return self.fee_pct / 100 * (1 + self.gst_on_fee_pct / 100)

    @property
    def effective_maker_fee(self) -> float:
        return self.maker_fee_pct / 100 * (1 + self.gst_on_fee_pct / 100)


@dataclass
class RiskConfig:
    # Fraction of equity risked between entry and stop on one trade.
    risk_per_trade_pct: float = field(default_factory=lambda: _env("RISK_PER_TRADE_PCT", 1.0))
    # Hard cap on position value as a fraction of equity.
    max_position_pct: float = field(default_factory=lambda: _env("MAX_POSITION_PCT", 100.0))
    # Hard cap on any single order value in quote currency (live safety net).
    max_order_value: float = field(default_factory=lambda: _env("MAX_ORDER_VALUE", 10000.0))
    # "daily": stops use the ATR of daily candles over `atr_days` (swing trading).
    # "bar": stops use the ATR of the trading candles over `atr_bars` (intraday).
    stop_atr_source: str = field(default_factory=lambda: _env("STOP_ATR_SOURCE", "daily"))
    atr_days: int = 14
    atr_bars: int = 14
    # Take profit at entry + N ATRs (0 = off).
    take_profit_atr_mult: float = field(default_factory=lambda: _env("TAKE_PROFIT_ATR_MULT", 0.0))
    # Holding horizon. min: the strategy may not exit sooner (stops still fire).
    # max: forced time exit; the signal must reset before re-entering. 0 = off.
    min_hold_hours: float = field(default_factory=lambda: _env("MIN_HOLD_HOURS", 0.0))
    max_hold_hours: float = field(default_factory=lambda: _env("MAX_HOLD_HOURS", 0.0))
    stop_atr_mult: float = field(default_factory=lambda: _env("STOP_ATR_MULT", 0.0))
    trailing_stop: bool = True
    daily_loss_limit_pct: float = field(default_factory=lambda: _env("DAILY_LOSS_LIMIT_PCT", 3.0))
    # Stop trading entirely if equity falls this far from its peak.
    max_drawdown_pct: float = field(default_factory=lambda: _env("MAX_DRAWDOWN_PCT", 35.0))
    # Hours to wait after a stop-out before re-entering.
    cooldown_hours: float = 24
    # Ignore target changes smaller than this (avoids churning fees on tiny rebalances).
    rebalance_threshold: float = 0.2


@dataclass
class TradingConfig:
    market: str = field(default_factory=lambda: _env("TRADING_MARKET", "BTCINR"))
    strategy: str = field(default_factory=lambda: _env("STRATEGY", "ensemble"))
    # Empty = the strategy's own default (1h for swing, 15m for intraday).
    interval: str = field(default_factory=lambda: _env("CANDLE_INTERVAL", ""))
    lookback: int = 400
    paper_starting_cash: float = field(default_factory=lambda: _env("PAPER_CASH", 100000.0))
    # Live: most quote currency (e.g. INR) the bot may put to work, counting its open
    # position. 0 = the whole free balance. Start small.
    capital_limit: float = field(default_factory=lambda: _env("CAPITAL_LIMIT", 5000.0))
    # Seconds a live limit order may rest before it is cancelled and re-priced.
    order_timeout_s: int = 20
    # Seconds a maker (resting bid) entry waits for a fill before it is cancelled.
    maker_wait_s: int = 300
    # Seconds between stop checks inside a bar.
    poll_s: int = 30
    state_db: str = field(default_factory=lambda: _env("STATE_DB", "coindcx_state.sqlite"))
    kill_switch_file: str = "STOP"


@dataclass
class AgentConfig:
    api: APIConfig = field(default_factory=APIConfig)
    costs: CostModel = field(default_factory=CostModel)
    risk: RiskConfig = field(default_factory=RiskConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    data_dir: str = field(default_factory=lambda: _env("DATA_DIR", "data"))


INTERVAL_SECONDS = {"1m": 60, "15m": 900, "1h": 3600, "1d": 86400}
