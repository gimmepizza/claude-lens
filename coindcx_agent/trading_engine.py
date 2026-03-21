"""Trading engine — orchestrates strategy signals, risk checks, and order execution."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from .api_client import CoinDCXClient, CoinDCXAPIError
from .config import AgentConfig
from .market_data import MarketDataFetcher
from .risk_manager import RiskManager
from .strategies.base import Strategy, Signal, TradeSignal


logger = logging.getLogger(__name__)


class PaperTrader:
    """Simulated order execution for paper trading."""

    def __init__(self):
        self.orders: list[dict] = []
        self.order_counter = 0

    def execute(self, market: str, side: str, quantity: float, price: float, order_type: str) -> dict:
        self.order_counter += 1
        order = {
            "id": f"paper-{self.order_counter}",
            "market": market,
            "side": side,
            "total_quantity": quantity,
            "price_per_unit": price,
            "order_type": order_type,
            "status": "filled",
            "timestamp": datetime.utcnow().isoformat(),
            "paper": True,
        }
        self.orders.append(order)
        return order


class TradingEngine:
    """Core trading engine that ties everything together.

    Runs the strategy loop: fetch data → analyze → risk check → execute.
    """

    def __init__(self, config: AgentConfig, strategy: Strategy):
        self.config = config
        self.client = CoinDCXClient(config.api)
        self.market_data = MarketDataFetcher(self.client)
        self.risk_manager = RiskManager(config.trading)
        self.strategy = strategy
        self.paper_trader = PaperTrader()
        self.trade_log: list[dict] = []
        self._running = False

    def _resolve_pair(self) -> str:
        """Resolve market symbol to the pair format needed by public endpoints."""
        pair = self.market_data.get_market_pair(self.config.trading.market)
        if not pair:
            raise ValueError(
                f"Market '{self.config.trading.market}' not found. "
                "Use get_markets_details() to see available markets."
            )
        return pair

    def _get_balance(self) -> float:
        """Get available balance for the quote currency."""
        if self.config.trading.paper_trading:
            return 100000.0  # 1 lakh simulated balance

        try:
            balances = self.client.get_balances()
            # Extract quote currency from market (e.g., INR from BTCINR)
            market_info = self.market_data.get_market_info(self.config.trading.market)
            if market_info:
                quote = market_info.get("target_currency_short_name", "INR")
            else:
                quote = "INR"

            for b in balances:
                if b.get("currency") == quote:
                    return float(b.get("balance", 0)) - float(b.get("locked_balance", 0))
        except CoinDCXAPIError as e:
            logger.error("Failed to fetch balances: %s", e)

        return 0.0

    def analyze(self) -> TradeSignal:
        """Run strategy analysis on current market data."""
        pair = self._resolve_pair()
        df = self.market_data.get_candles_df(
            pair=pair,
            interval=self.config.trading.candle_interval,
            limit=self.config.trading.lookback_candles,
        )

        if df.empty or len(df) < 30:
            return TradeSignal(
                signal=Signal.HOLD,
                strategy=self.strategy.name,
                confidence=0.0,
                price=0.0,
                reason="Insufficient market data",
                indicators={},
            )

        return self.strategy.analyze(df)

    def execute_signal(self, signal: TradeSignal) -> dict | None:
        """Execute a trade signal after risk checks."""
        if signal.signal == Signal.HOLD:
            logger.info("HOLD signal — no action taken")
            return None

        balance = self._get_balance()
        allowed, reason = self.risk_manager.check_trade_allowed(signal, balance)
        if not allowed:
            logger.info("Trade rejected: %s", reason)
            return None

        position = self.risk_manager.calculate_position_size(signal, balance, signal.price)
        if not position.approved:
            logger.info("Position rejected: %s", position.rejection_reason)
            return None

        logger.info(
            "Executing %s %s: qty=%.6f @ %.2f (SL=%.2f, TP=%.2f, risk=%.2f)",
            signal.signal.value.upper(),
            self.config.trading.market,
            position.quantity,
            signal.price,
            position.stop_loss_price,
            position.take_profit_price,
            position.risk_amount,
        )

        order = self._place_order(
            side=signal.signal.value,
            quantity=position.quantity,
            price=signal.price,
        )

        if order:
            self.risk_manager.record_trade(
                self.config.trading.market,
                signal.signal.value,
                position.quantity,
                signal.price,
            )
            self._log_trade(signal, position, order)

        return order

    def _place_order(self, side: str, quantity: float, price: float) -> dict | None:
        """Place an order via API or paper trader."""
        if self.config.trading.paper_trading:
            return self.paper_trader.execute(
                market=self.config.trading.market,
                side=side,
                quantity=quantity,
                price=price,
                order_type=self.config.trading.order_type,
            )

        try:
            return self.client.create_order(
                market=self.config.trading.market,
                side=side,
                order_type=self.config.trading.order_type,
                total_quantity=quantity,
                price_per_unit=price,
            )
        except CoinDCXAPIError as e:
            logger.error("Order failed: %s", e)
            return None

    def _log_trade(self, signal: TradeSignal, position, order: dict):
        """Log trade to file and memory."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "market": self.config.trading.market,
            "signal": signal.signal.value,
            "strategy": signal.strategy,
            "confidence": signal.confidence,
            "reason": signal.reason,
            "price": signal.price,
            "quantity": position.quantity,
            "value": position.value,
            "stop_loss": position.stop_loss_price,
            "take_profit": position.take_profit_price,
            "risk_amount": position.risk_amount,
            "order_id": order.get("id", "unknown"),
            "paper": self.config.trading.paper_trading,
            "indicators": signal.indicators,
        }
        self.trade_log.append(entry)

        if self.config.log_trades:
            log_path = Path(self.config.trade_log_file)
            existing = []
            if log_path.exists():
                try:
                    existing = json.loads(log_path.read_text())
                except (json.JSONDecodeError, IOError):
                    pass
            existing.append(entry)
            log_path.write_text(json.dumps(existing, indent=2, default=str))

    def run_once(self) -> dict:
        """Run a single analysis + execution cycle. Returns a summary dict."""
        signal = self.analyze()
        order = self.execute_signal(signal)

        return {
            "signal": signal.signal.value,
            "strategy": signal.strategy,
            "confidence": signal.confidence,
            "price": signal.price,
            "reason": signal.reason,
            "indicators": signal.indicators,
            "order": order,
            "paper": self.config.trading.paper_trading,
        }

    def run_loop(self, interval_seconds: int = 60):
        """Run the trading loop continuously."""
        self._running = True
        logger.info(
            "Starting trading loop: market=%s, strategy=%s, interval=%ds, paper=%s",
            self.config.trading.market,
            self.strategy.name,
            interval_seconds,
            self.config.trading.paper_trading,
        )

        while self._running:
            try:
                result = self.run_once()
                logger.info(
                    "[%s] %s | confidence=%.2f | price=%.2f | %s",
                    result["strategy"],
                    result["signal"].upper(),
                    result["confidence"],
                    result["price"],
                    result["reason"],
                )
            except Exception as e:
                logger.error("Error in trading loop: %s", e, exc_info=True)

            time.sleep(interval_seconds)

    def stop(self):
        """Stop the trading loop."""
        self._running = False
        logger.info("Trading loop stopped")

    def get_portfolio_summary(self) -> dict:
        """Get current portfolio summary."""
        pair = self._resolve_pair()
        ticker = self.market_data.get_ticker_for_market(self.config.trading.market)
        spread = self.market_data.get_spread(pair)

        return {
            "market": self.config.trading.market,
            "paper_trading": self.config.trading.paper_trading,
            "strategy": self.strategy.name,
            "balance": self._get_balance(),
            "open_positions": self.risk_manager.open_positions,
            "daily_trades": self.risk_manager.daily_trades,
            "daily_loss": self.risk_manager.daily_loss,
            "total_trades": len(self.trade_log),
            "ticker": ticker,
            "spread": spread,
        }
