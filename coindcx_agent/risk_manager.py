"""Risk management and position sizing for the trading agent."""

import logging
from dataclasses import dataclass

from .config import TradingConfig
from .strategies.base import Signal, TradeSignal


logger = logging.getLogger(__name__)


@dataclass
class PositionSize:
    """Calculated position size with risk parameters."""
    quantity: float
    value: float
    stop_loss_price: float
    take_profit_price: float
    risk_amount: float
    risk_reward_ratio: float
    approved: bool
    rejection_reason: str = ""


class RiskManager:
    """Manages trade risk, position sizing, and portfolio exposure."""

    def __init__(self, config: TradingConfig):
        self.config = config
        self.open_positions: dict[str, dict] = {}
        self.daily_loss: float = 0.0
        self.daily_trades: int = 0
        self.max_daily_trades: int = 50
        self.max_daily_loss_pct: float = config.max_loss_pct * 2

    def calculate_position_size(
        self,
        signal: TradeSignal,
        available_balance: float,
        current_price: float,
    ) -> PositionSize:
        """Calculate position size based on risk parameters.

        Uses a percentage-of-portfolio approach with stop-loss based sizing.
        """
        # Max position value as % of portfolio
        max_position_value = available_balance * (self.config.max_position_size_pct / 100)

        # Scale position by signal confidence
        position_value = max_position_value * signal.confidence

        # Minimum position check
        if position_value < 1.0:
            return PositionSize(
                quantity=0, value=0, stop_loss_price=0, take_profit_price=0,
                risk_amount=0, risk_reward_ratio=0, approved=False,
                rejection_reason="Position value too small",
            )

        # Calculate stop-loss and take-profit
        risk_pct = self.config.max_loss_pct / 100
        reward_pct = risk_pct * 2  # 1:2 risk-reward ratio

        if signal.signal == Signal.BUY:
            stop_loss_price = current_price * (1 - risk_pct)
            take_profit_price = current_price * (1 + reward_pct)
        else:
            stop_loss_price = current_price * (1 + risk_pct)
            take_profit_price = current_price * (1 - reward_pct)

        quantity = position_value / current_price
        risk_amount = position_value * risk_pct

        return PositionSize(
            quantity=quantity,
            value=position_value,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            risk_amount=risk_amount,
            risk_reward_ratio=2.0,
            approved=True,
        )

    def check_trade_allowed(
        self,
        signal: TradeSignal,
        available_balance: float,
    ) -> tuple[bool, str]:
        """Run pre-trade risk checks."""
        # Paper trading always allowed
        if self.config.paper_trading:
            return True, "Paper trading mode"

        # Daily trade limit
        if self.daily_trades >= self.max_daily_trades:
            return False, f"Daily trade limit reached ({self.max_daily_trades})"

        # Daily loss limit
        if self.daily_loss >= available_balance * (self.max_daily_loss_pct / 100):
            return False, f"Daily loss limit reached ({self.max_daily_loss_pct}%)"

        # Minimum confidence threshold
        if signal.confidence < 0.2:
            return False, f"Signal confidence too low ({signal.confidence:.2f})"

        # Don't trade HOLD signals
        if signal.signal == Signal.HOLD:
            return False, "Signal is HOLD"

        # Check existing position conflict
        market = self.config.market
        if market in self.open_positions:
            existing_side = self.open_positions[market].get("side")
            if signal.signal.value == existing_side:
                return False, f"Already have a {existing_side} position in {market}"

        return True, "Trade approved"

    def record_trade(self, market: str, side: str, quantity: float, price: float):
        """Record an executed trade."""
        self.daily_trades += 1
        self.open_positions[market] = {
            "side": side,
            "quantity": quantity,
            "entry_price": price,
        }
        logger.info("Recorded trade: %s %s %.6f @ %.2f", side, market, quantity, price)

    def record_close(self, market: str, exit_price: float):
        """Record a closed position and update P&L."""
        if market not in self.open_positions:
            return

        pos = self.open_positions.pop(market)
        if pos["side"] == "buy":
            pnl = (exit_price - pos["entry_price"]) * pos["quantity"]
        else:
            pnl = (pos["entry_price"] - exit_price) * pos["quantity"]

        if pnl < 0:
            self.daily_loss += abs(pnl)

        logger.info("Closed position in %s: P&L = %.2f", market, pnl)

    def reset_daily(self):
        """Reset daily counters (call at start of each trading day)."""
        self.daily_loss = 0.0
        self.daily_trades = 0
