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

## Intraday: 30 minute – 3 hour trades

`breakout`, `rsi2`, `vwap_revert` and `squeeze` run on 15m candles with a fixed horizon:

- **Min hold 30 min:** the strategy can't exit sooner (stops still fire).
- **Max hold 3 h:** a time exit; after it, the signal must reset before re-entering.
- **Stop 2× / take-profit 3× the 15m ATR**, 1 h cooldown after a stop.
- **Optional maker entries** (`--maker`): rest a bid instead of crossing the spread. In the
  backtest it only fills if price trades *through* the bid; misses are counted.

Override any of these with `--min-hold`, `--max-hold`, `--stop`, `--take-profit`,
`--stop-source`, or the matching `.env` values.

```bash
python -m coindcx_agent compare -m BTCUSDT -i 15m --fee 0.1 --maker --maker-fee 0
python -m coindcx_agent backtest -m BTCUSDT -s rsi2 --report rsi2.html
python -m coindcx_agent paper -m BTCUSDT -s breakout
```

**Backtest verdict (Nov 2024 – Nov 2026, BTC/ETH/SOL USDT and BTCINR): none of them
make money.** Even with zero costs, the average trade earns between −0.05% and +0.03%.
That's no edge. The cheapest realistic round trip (0.1% taker, 0% maker, plus GST and
slippage) costs ~0.12–0.15%. Every strategy loses 50–90% over two years. A daily-trend
filter doesn't fix it.

Two more things matter at this horizon:
- **Use USDT markets, not INR.** INR spreads are 0.5–0.7%, about the size of a typical 3h
  move. BTCUSDT and ETHUSDT spreads are about 0%.
- **Indian tax makes frequent trading worse.** Each winning trade is taxed with no loss
  set-off, so the estimated tax can exceed what's left of your capital ("after tax" below −100%).

Treat these as a research harness. Don't take them live unless you find an idea that
survives `compare --walk-forward` after costs.

## How it works

| Module | Job |
|---|---|
| `exchange.py` | REST client: HMAC signing, timeouts, retries with backoff, rate limit; never blind-retries order creation. `MarketRules` rounds quantity/price to exchange precision and checks minimum order value. |
| `data.py` | Paginated candle history with a CSV cache; drops the still-forming candle. |
| `indicators.py` | EMA, RSI, ATR, Bollinger, MACD, Donchian, ADX, realized vol, daily ATR. |
| `strategies.py` | Each strategy returns a target exposure in [0, 1] for every bar. |
| `risk.py` | Sizing, ATR stop (daily or bar), take-profit, min/max holding time, cooldown, daily loss limit, drawdown kill switch. Shared by backtest and live. |
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
| `breakout` | intraday | Close above the last 4h high on 1.5× volume, in a 1-day uptrend |
| `rsi2` | intraday | Buy RSI(2) < 10 in an uptrend, exit when RSI(2) > 70 |
| `vwap_revert` | intraday | Buy 2 std-devs below the 24h rolling VWAP, exit at VWAP |
| `squeeze` | intraday | Buy the upside break after a Bollinger-band squeeze |
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
