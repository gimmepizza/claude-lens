# CoinDCX algo trading agent (v2)

A long-only spot trading bot for CoinDCX with an honest backtester. It is built so
that **what you backtest is exactly what you trade**, and so that a mistake costs
as little as possible.

> Crypto trading can lose you money. Backtests are not predictions. Paper-trade
> first, then go live with a small `CAPITAL_LIMIT`. Tax figures are rough
> estimates under India's VDA rules, not tax advice.

## Quick start

```bash
pip install -r coindcx_agent/requirements.txt
cp coindcx_agent/.env.example .env      # API keys only needed for balance/live

python -m coindcx_agent markets --search INR          # what's tradable, by volume
python -m coindcx_agent compare -m BTCINR -i 1d --walk-forward
python -m coindcx_agent backtest -m BTCINR -i 1d -s ema_cross --report report.html
python -m coindcx_agent signal -m BTCINR               # what would it do right now?
python -m coindcx_agent paper -m BTCINR                # paper trade, live prices
python -m coindcx_agent status -m BTCINR               # equity, fills, events
```

Going live needs three deliberate steps: API keys in `.env`,
`LIVE_TRADING_CONFIRM=I_ACCEPT_THE_RISK` in the environment, and typing the market
name at the prompt.

```bash
python -m coindcx_agent live -m BTCINR --capital-limit 5000 --max-order-value 5000
```

## What the backtests say (Nov 2026, daily candles, ~3 years)

Run `compare --walk-forward` yourself; results move as new data arrives.

- **Costs decide everything.** At the default 0.5% fee + GST + 0.3% spread, a round
  trip costs ~1.6%. At a 0.1% fee most trend strategies beat buy & hold
  out-of-sample on BTCINR; at 0.5% only `ema_cross`/`donchian` do. **Check your fee tier.**
- **Decide on daily candles.** Multi-day signals evaluated hourly whipsaw and bleed
  fees. Strategies therefore decide on completed daily candles by default, even when
  the bot runs on 1h candles (which then only speed up stops and kill-switch checks).
- **Trend filters mostly cut drawdowns.** Typical max drawdown -25…-35% vs -47…-74%
  for holding. They do not reliably beat holding on raw return, and results differ a
  lot between coins (EMA cross: great on BTC/ETH INR, poor on SOL).
- **Mean reversion (RSI, Bollinger) doesn't survive these costs.** Kept for research.
- **Tight stops hurt.** Price stops sized from hourly ATR were hit by noise on almost
  every trade. Stops are off by default; the strategy exits act as stops, and a
  drawdown kill switch backs them up. Enable with `--stop 5` (daily ATRs) if you want one.
- **Indian tax changes the picture.** Each profitable sale is taxed at 30% + cess with
  no loss set-off, while buy & hold is only taxed when sold. Compare the
  "after tax" column, not just "return".

## How it works

| Module | Job |
|---|---|
| `exchange.py` | REST client: HMAC signing, timeouts, retries with backoff, rate limit; never blind-retries order creation. `MarketRules` rounds quantity/price to exchange precision and checks minimum order value. |
| `data.py` | Paginated candle history with a CSV cache; drops the still-forming candle. |
| `indicators.py` | EMA, RSI, ATR, Bollinger, MACD, Donchian, ADX, realized vol, daily ATR. |
| `strategies.py` | Each strategy returns a target exposure in [0, 1] for every bar. |
| `risk.py` | Sizing, optional ATR trailing stop, cooldown, daily loss limit, drawdown kill switch. Shared by backtest and live. |
| `backtest.py` | Bar-by-bar simulator + walk-forward optimiser. |
| `brokers.py` | `PaperBroker` (fills at live bid/ask + slippage + fees) and `LiveBroker`. |
| `engine.py` | The trading loop. |
| `state.py` | SQLite: positions, fills, equity, risk state, events. Survives restarts. |
| `report.py` | Self-contained HTML report (equity and drawdown vs buy & hold). |

### Backtest rules

- A signal from bar *t*'s close is filled at bar *t+1*'s open.
- Every fill pays half the spread + slippage + fee + 18% GST on the fee.
- Stops are checked against the bar's low; a gap through the stop fills at the open.
- 1% TDS on INR sales is reported (it's creditable); estimated tax = 31.2% of each
  sale's gain.
- Walk-forward: parameters are re-chosen on the previous 365 days and traded on the
  next 90 unseen days; only those unseen periods are stitched into the result.

### Live safety

- **Your existing coins are never touched.** The bot tracks the quantity *it* bought
  and only ever sells that.
- `CAPITAL_LIMIT` caps how much quote currency the bot may use (default ₹5,000).
- `MAX_ORDER_VALUE` caps any single order.
- Orders are marketable limit orders at the best bid/ask (price-protected); unfilled
  remainders are cancelled after `order_timeout_s`. A failed create is looked up by
  client order ID instead of being resent, so it can't double-buy.
- Kill switches: drawdown ≥ `MAX_DRAWDOWN_PCT` flattens and halts until you run
  `reset-halt`; a file named `STOP` in the working directory stops the loop;
  `DAILY_LOSS_LIMIT_PCT` blocks new buying for the rest of the IST day.
- On restart the bot reloads its state and does not re-trade a candle it already acted on.

## Strategies

| Name | Type | Idea |
|---|---|---|
| `ensemble` (default) | trend | Average of `trend_vol`, `donchian`, `ema_cross` |
| `ema_cross` | trend | Fast EMA above slow EMA, with ADX trend-strength filter |
| `donchian` | trend | Buy an N-day high breakout, exit at an M-day low |
| `trend_vol` | trend | Multi-horizon momentum, volatility-targeted size, stepped exposure |
| `macd` | momentum | MACD above signal and above zero |
| `rsi_dip` | mean reversion | Buy RSI dips inside an uptrend |
| `bollinger` | mean reversion | Buy below the lower band, exit at the middle |

Override parameters with `--params '{"entry_days": 40, "exit_days": 20}'`.

## Configuration (`.env`)

See `.env.example`. Every value can also be set with a CLI flag (`--help` on any command).

## Running it 24/7

The paper/live loop is a single process. Run it under `tmux`, `systemd` or a small VM,
for example:

```bash
nohup python -m coindcx_agent paper -m BTCINR > bot.log 2>&1 &
touch STOP     # graceful stop at the next check
```

## Tests

```bash
python -m pytest coindcx_agent/tests -q
```

They cover exchange rounding and signing, candle parsing, lookahead (every strategy's
signal at bar k is identical with or without future bars), backtest accounting
against a vectorized reference, risk rules, and the engine and brokers against a fake
exchange (including "never sells pre-existing coins").
