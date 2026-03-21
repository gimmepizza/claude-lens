"""CoinDCX Quant Algo Trading Agent — main CLI entry point."""

import argparse
import json
import logging
import signal
import sys
from datetime import datetime

from colorama import Fore, Style, init as colorama_init
from tabulate import tabulate

from .config import AgentConfig, StrategyParams
from .api_client import CoinDCXClient
from .market_data import MarketDataFetcher
from .trading_engine import TradingEngine
from .strategies.base import Signal
from .strategies.ema_crossover import EMACrossoverStrategy
from .strategies.rsi_strategy import RSIStrategy
from .strategies.bollinger_bands import BollingerBandsStrategy
from .strategies.vwap_strategy import VWAPStrategy
from .strategies.macd_strategy import MACDStrategy
from .strategies.composite import CompositeStrategy


colorama_init()

STRATEGIES = {
    "ema_crossover": EMACrossoverStrategy,
    "rsi": RSIStrategy,
    "bollinger_bands": BollingerBandsStrategy,
    "vwap": VWAPStrategy,
    "macd": MACDStrategy,
    "composite": CompositeStrategy,
}

BANNER = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║         CoinDCX Quant Algo Trading Agent v1.0.0              ║
║                                                              ║
║  Strategies: EMA Crossover │ RSI │ Bollinger Bands           ║
║              VWAP │ MACD │ Composite (multi-signal)          ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s │ %(levelname)-8s │ %(message)s",
        datefmt="%H:%M:%S",
    )


def get_strategy(name: str, params: StrategyParams):
    cls = STRATEGIES.get(name)
    if not cls:
        print(f"{Fore.RED}Unknown strategy: {name}{Style.RESET_ALL}")
        print(f"Available: {', '.join(STRATEGIES.keys())}")
        sys.exit(1)
    return cls(params)


def color_signal(signal_val: str) -> str:
    colors = {"buy": Fore.GREEN, "sell": Fore.RED, "hold": Fore.YELLOW}
    color = colors.get(signal_val, "")
    return f"{color}{signal_val.upper()}{Style.RESET_ALL}"


# ── Commands ────────────────────────────────────────────────────


def cmd_analyze(engine: TradingEngine):
    """Run a single analysis cycle and display results."""
    print(f"\n{Fore.CYAN}Analyzing {engine.config.trading.market}...{Style.RESET_ALL}\n")

    result = engine.run_once()

    signal_colored = color_signal(result["signal"])
    mode = f"{Fore.YELLOW}PAPER{Style.RESET_ALL}" if result["paper"] else f"{Fore.RED}LIVE{Style.RESET_ALL}"

    print(f"  Mode:       {mode}")
    print(f"  Market:     {engine.config.trading.market}")
    print(f"  Strategy:   {result['strategy']}")
    print(f"  Signal:     {signal_colored}")
    print(f"  Confidence: {result['confidence']:.2%}")
    print(f"  Price:      {result['price']:.2f}")
    print(f"  Reason:     {result['reason']}")

    if result["order"]:
        print(f"\n  {Fore.GREEN}Order placed:{Style.RESET_ALL}")
        print(f"    ID:       {result['order'].get('id', 'N/A')}")
        print(f"    Qty:      {result['order'].get('total_quantity', 'N/A')}")
        print(f"    Price:    {result['order'].get('price_per_unit', 'N/A')}")

    if result["indicators"]:
        print(f"\n  {Fore.CYAN}Indicators:{Style.RESET_ALL}")
        for key, val in result["indicators"].items():
            if isinstance(val, dict):
                print(f"    {key}:")
                for k2, v2 in val.items():
                    print(f"      {k2}: {v2}")
            elif isinstance(val, float):
                print(f"    {key}: {val:.6f}")
            else:
                print(f"    {key}: {val}")
    print()


def cmd_run(engine: TradingEngine, interval: int):
    """Run the continuous trading loop."""
    mode = "PAPER" if engine.config.trading.paper_trading else "LIVE"
    print(f"\n{Fore.CYAN}Starting {mode} trading loop{Style.RESET_ALL}")
    print(f"  Market:   {engine.config.trading.market}")
    print(f"  Strategy: {engine.strategy.name}")
    print(f"  Interval: {interval}s")
    print(f"\n  Press Ctrl+C to stop.\n")

    def handle_sigint(sig, frame):
        engine.stop()
        print(f"\n{Fore.YELLOW}Shutting down...{Style.RESET_ALL}")

    signal.signal(signal.SIGINT, handle_sigint)
    engine.run_loop(interval_seconds=interval)


def cmd_ticker(engine: TradingEngine):
    """Display current ticker data."""
    print(f"\n{Fore.CYAN}Fetching ticker for {engine.config.trading.market}...{Style.RESET_ALL}\n")
    ticker = engine.market_data.get_ticker_for_market(engine.config.trading.market)
    if ticker:
        rows = [[k, v] for k, v in ticker.items()]
        print(tabulate(rows, headers=["Field", "Value"], tablefmt="simple"))
    else:
        print(f"{Fore.RED}Market not found{Style.RESET_ALL}")
    print()


def cmd_orderbook(engine: TradingEngine):
    """Display current order book."""
    pair = engine._resolve_pair()
    print(f"\n{Fore.CYAN}Order book for {engine.config.trading.market} ({pair}){Style.RESET_ALL}\n")

    spread = engine.market_data.get_spread(pair)
    print(f"  Best Bid: {spread['best_bid']:.2f}")
    print(f"  Best Ask: {spread['best_ask']:.2f}")
    print(f"  Spread:   {spread['spread']:.2f} ({spread['spread_pct']:.4f}%)\n")

    book = engine.market_data.get_orderbook_df(pair)
    print(f"  {Fore.GREEN}Top Bids:{Style.RESET_ALL}")
    if not book["bids"].empty:
        print(tabulate(book["bids"].head(10), headers="keys", tablefmt="simple", showindex=False))
    print(f"\n  {Fore.RED}Top Asks:{Style.RESET_ALL}")
    if not book["asks"].empty:
        print(tabulate(book["asks"].head(10), headers="keys", tablefmt="simple", showindex=False))
    print()


def cmd_balance(engine: TradingEngine):
    """Display account balances."""
    if engine.config.trading.paper_trading:
        print(f"\n{Fore.YELLOW}Paper trading mode — simulated balance: ₹100,000{Style.RESET_ALL}\n")
        return

    print(f"\n{Fore.CYAN}Fetching balances...{Style.RESET_ALL}\n")
    balances = engine.client.get_balances()
    non_zero = [b for b in balances if float(b.get("balance", 0)) > 0]

    if non_zero:
        rows = [
            [b["currency"], b["balance"], b.get("locked_balance", 0)]
            for b in non_zero
        ]
        print(tabulate(rows, headers=["Currency", "Balance", "Locked"], tablefmt="simple"))
    else:
        print("No non-zero balances found.")
    print()


def cmd_markets(engine: TradingEngine, search: str = ""):
    """List available markets."""
    print(f"\n{Fore.CYAN}Fetching markets...{Style.RESET_ALL}\n")
    details = engine.market_data.get_all_market_details()

    if search:
        details = [d for d in details if search.upper() in d.get("symbol", "").upper()]

    rows = [
        [
            d.get("symbol", ""),
            d.get("base_currency_short_name", ""),
            d.get("target_currency_short_name", ""),
            d.get("min_quantity", ""),
            d.get("max_quantity", ""),
            d.get("status", ""),
        ]
        for d in details[:50]
    ]
    print(tabulate(
        rows,
        headers=["Symbol", "Base", "Quote", "Min Qty", "Max Qty", "Status"],
        tablefmt="simple",
    ))
    print(f"\n  Showing {len(rows)} of {len(details)} markets\n")


def cmd_portfolio(engine: TradingEngine):
    """Display portfolio summary."""
    print(f"\n{Fore.CYAN}Portfolio Summary{Style.RESET_ALL}\n")
    summary = engine.get_portfolio_summary()

    rows = [
        ["Market", summary["market"]],
        ["Mode", "PAPER" if summary["paper_trading"] else "LIVE"],
        ["Strategy", summary["strategy"]],
        ["Balance", f"{summary['balance']:.2f}"],
        ["Daily Trades", summary["daily_trades"]],
        ["Total Trades", summary["total_trades"]],
        ["Daily Loss", f"{summary['daily_loss']:.2f}"],
    ]
    print(tabulate(rows, tablefmt="simple"))

    if summary["spread"]:
        print(f"\n  Spread: {summary['spread']['spread']:.2f} ({summary['spread']['spread_pct']:.4f}%)")

    if summary["open_positions"]:
        print(f"\n  {Fore.CYAN}Open Positions:{Style.RESET_ALL}")
        for market, pos in summary["open_positions"].items():
            print(f"    {market}: {pos['side']} {pos['quantity']:.6f} @ {pos['entry_price']:.2f}")
    print()


def cmd_trades(engine: TradingEngine):
    """Display trade log."""
    print(f"\n{Fore.CYAN}Trade History{Style.RESET_ALL}\n")

    if not engine.trade_log:
        print("  No trades executed this session.\n")
        return

    rows = [
        [
            t["timestamp"][:19],
            color_signal(t["signal"]),
            t["strategy"],
            f"{t['confidence']:.2%}",
            f"{t['price']:.2f}",
            f"{t['quantity']:.6f}",
            "✓" if t.get("paper") else "LIVE",
        ]
        for t in engine.trade_log
    ]
    print(tabulate(
        rows,
        headers=["Time", "Signal", "Strategy", "Conf.", "Price", "Qty", "Mode"],
        tablefmt="simple",
    ))
    print()


# ── Main ────────────────────────────────────────────────────────


def main():
    print(BANNER)

    parser = argparse.ArgumentParser(
        description="CoinDCX Quant Algo Trading Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "command",
        choices=["analyze", "run", "ticker", "orderbook", "balance", "markets", "portfolio", "trades"],
        help="Command to execute",
    )
    parser.add_argument("-m", "--market", default=None, help="Trading market (e.g., BTCINR)")
    parser.add_argument(
        "-s", "--strategy",
        default=None,
        choices=list(STRATEGIES.keys()),
        help="Trading strategy to use",
    )
    parser.add_argument("-i", "--interval", type=int, default=60, help="Loop interval in seconds (default: 60)")
    parser.add_argument("--search", default="", help="Search filter for markets command")
    parser.add_argument("--paper", action="store_true", default=None, help="Enable paper trading")
    parser.add_argument("--live", action="store_true", help="Enable live trading (requires API keys)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Build config
    config = AgentConfig()
    if args.market:
        config.trading.market = args.market
    if args.strategy:
        config.trading.default_strategy = args.strategy
    if args.paper:
        config.trading.paper_trading = True
    if args.live:
        config.trading.paper_trading = False
        if not config.api.api_key or not config.api.api_secret:
            print(f"{Fore.RED}ERROR: Live trading requires COINDCX_API_KEY and COINDCX_API_SECRET{Style.RESET_ALL}")
            print("Set them in your .env file or environment variables.")
            sys.exit(1)

    # Build strategy
    strategy = get_strategy(config.trading.default_strategy, config.strategy_params)

    # Build engine
    engine = TradingEngine(config, strategy)

    # Dispatch command
    commands = {
        "analyze": lambda: cmd_analyze(engine),
        "run": lambda: cmd_run(engine, args.interval),
        "ticker": lambda: cmd_ticker(engine),
        "orderbook": lambda: cmd_orderbook(engine),
        "balance": lambda: cmd_balance(engine),
        "markets": lambda: cmd_markets(engine, args.search),
        "portfolio": lambda: cmd_portfolio(engine),
        "trades": lambda: cmd_trades(engine),
    }

    try:
        commands[args.command]()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
