"""Configuration management for the CoinDCX trading agent."""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv


load_dotenv()


@dataclass
class APIConfig:
    """CoinDCX API configuration."""
    api_key: str = ""
    api_secret: str = ""
    base_url: str = "https://api.coindcx.com"
    public_url: str = "https://public.coindcx.com"

    def __post_init__(self):
        self.api_key = self.api_key or os.getenv("COINDCX_API_KEY", "")
        self.api_secret = self.api_secret or os.getenv("COINDCX_API_SECRET", "")


@dataclass
class TradingConfig:
    """Trading parameters configuration."""
    market: str = ""
    default_strategy: str = "ema_crossover"
    max_position_size_pct: float = 5.0
    max_loss_pct: float = 2.0
    paper_trading: bool = True
    candle_interval: str = "5m"
    lookback_candles: int = 100
    order_type: str = "limit_order"

    def __post_init__(self):
        self.market = self.market or os.getenv("TRADING_MARKET", "BTCINR")
        self.default_strategy = os.getenv("DEFAULT_STRATEGY", self.default_strategy)
        self.max_position_size_pct = float(
            os.getenv("MAX_POSITION_SIZE_PCT", self.max_position_size_pct)
        )
        self.max_loss_pct = float(os.getenv("MAX_LOSS_PCT", self.max_loss_pct))
        self.paper_trading = os.getenv("PAPER_TRADING", "true").lower() == "true"


@dataclass
class StrategyParams:
    """Strategy-specific parameters."""
    # EMA Crossover
    ema_fast_period: int = 9
    ema_slow_period: int = 21

    # RSI
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0

    # Bollinger Bands
    bb_period: int = 20
    bb_std_dev: float = 2.0

    # VWAP
    vwap_deviation: float = 1.5

    # MACD
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9


@dataclass
class AgentConfig:
    """Top-level agent configuration."""
    api: APIConfig = field(default_factory=APIConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    strategy_params: StrategyParams = field(default_factory=StrategyParams)
    log_trades: bool = True
    trade_log_file: str = "trades.json"
