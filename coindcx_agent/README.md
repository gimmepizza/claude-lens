# CoinDCX Quant Algo Trading Agent

A Python-based quantitative algorithmic trading agent for the CoinDCX cryptocurrency exchange. Supports multiple technical analysis strategies, risk management, paper trading, and live order execution via the CoinDCX REST API.

## Features

- **6 Trading Strategies**: EMA Crossover, RSI, Bollinger Bands, VWAP, MACD, and a Composite multi-signal strategy
- **Full CoinDCX API Integration**: HMAC-SHA256 authenticated REST API client for orders, balances, market data
- **Risk Management**: Position sizing, stop-loss/take-profit, daily loss limits, trade frequency limits
- **Paper Trading**: Simulated execution for strategy testing without risking real funds
- **Live Trading**: Execute real orders on CoinDCX with proper authentication
- **Technical Indicators**: EMA, SMA, RSI, Bollinger Bands, MACD, VWAP, ATR, Stochastic RSI, OBV
- **Trade Logging**: All trades logged to JSON for analysis
- **CLI Interface**: Full-featured command-line interface

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys (copy and edit)
cp .env.example .env
# Edit .env with your CoinDCX API key and secret
```

## Usage

```bash
# Run a single analysis (paper mode by default)
python -m coindcx_agent analyze -m BTCINR -s ema_crossover

# Run continuous trading loop
python -m coindcx_agent run -m BTCINR -s composite -i 60

# View ticker data
python -m coindcx_agent ticker -m BTCINR

# View order book
python -m coindcx_agent orderbook -m BTCINR

# List available markets
python -m coindcx_agent markets --search BTC

# View portfolio summary
python -m coindcx_agent portfolio -m BTCINR

# View trade history
python -m coindcx_agent trades

# Check balances (live mode)
python -m coindcx_agent balance --live

# Live trading (requires API keys in .env)
python -m coindcx_agent run -m BTCINR -s composite --live -i 120
```

## Strategies

| Strategy | Type | Description |
|---|---|---|
| `ema_crossover` | Trend Following | Buy on fast EMA crossing above slow EMA, sell on cross below |
| `rsi` | Mean Reversion | Buy when RSI < 30 (oversold), sell when RSI > 70 (overbought) |
| `bollinger_bands` | Mean Reversion | Buy at lower band, sell at upper band |
| `vwap` | Value | Buy below VWAP, sell above VWAP |
| `macd` | Momentum | Buy/sell on MACD-signal line crossovers |
| `composite` | Multi-Signal | Combines all strategies; trades only when 3+ agree |

## Configuration

Environment variables (`.env`):

| Variable | Default | Description |
|---|---|---|
| `COINDCX_API_KEY` | — | Your CoinDCX API key |
| `COINDCX_API_SECRET` | — | Your CoinDCX API secret |
| `TRADING_MARKET` | `BTCINR` | Default trading market |
| `DEFAULT_STRATEGY` | `ema_crossover` | Default strategy |
| `MAX_POSITION_SIZE_PCT` | `5.0` | Max position as % of portfolio |
| `MAX_LOSS_PCT` | `2.0` | Max loss per trade (%) |
| `PAPER_TRADING` | `true` | Paper trading mode |

## Project Structure

```
coindcx_agent/
├── __init__.py          # Package init
├── __main__.py          # Entry point for python -m
├── agent.py             # CLI agent with all commands
├── api_client.py        # CoinDCX REST API client (HMAC auth)
├── config.py            # Configuration management
├── market_data.py       # Market data fetching & processing
├── risk_manager.py      # Risk management & position sizing
├── trading_engine.py    # Core trading engine
├── strategies/
│   ├── base.py              # Strategy interface & signal types
│   ├── ema_crossover.py     # EMA Crossover strategy
│   ├── rsi_strategy.py      # RSI strategy
│   ├── bollinger_bands.py   # Bollinger Bands strategy
│   ├── vwap_strategy.py     # VWAP strategy
│   ├── macd_strategy.py     # MACD strategy
│   └── composite.py         # Multi-strategy composite
├── utils/
│   └── indicators.py        # Technical indicator calculations
├── .env.example         # Environment template
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## API Endpoints Used

**Public (no auth):**
- `GET /exchange/ticker` — Market ticker
- `GET /exchange/v1/markets_details` — Market info
- `GET /market_data/candles` — OHLCV candles
- `GET /market_data/orderbook` — Order book
- `GET /market_data/trade_history` — Recent trades

**Private (HMAC-SHA256 auth):**
- `POST /exchange/v1/users/balances` — Account balances
- `POST /exchange/v1/orders/create` — Place order
- `POST /exchange/v1/orders/cancel` — Cancel order
- `POST /exchange/v1/orders/active_orders` — Active orders
- `POST /exchange/v1/orders/trade_history` — Trade history

## Risk Disclaimer

This software is for educational and research purposes. Cryptocurrency trading involves substantial risk of loss. Always start with paper trading and never risk more than you can afford to lose.
