# LIQUIDITY HUNTER AI — Binance Futures SMC Scanner

A research-only Binance USDⓈ-M perpetual futures scanner and web dashboard.

## Futures SMC scanner
- Discovers all active USDT-margined perpetual contracts from Binance Futures exchange metadata.
- Scans liquid contracts (default minimum 24h quote volume: 5,000,000 USDT) using completed 5-minute candles.
- Uses liquidity sweeps, displacement, market-structure breaks, FVG context, EMA trend, relative volume, taker-buy ratio, open-interest change and funding.
- Returns LONG / SHORT / NO TRADE with reasons, scores and an ATR-based example stop.
- Dashboard refreshes every five minutes while open; optional Telegram alerts are sent for newly detected LONG/SHORT signals.
- Telegram configuration: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.

## Risk defaults
- Assumed research equity: INR 10,000
- Maximum planned risk per trade: 0.25% (INR 25)
- Daily loss stop: 0.5% (INR 50)
- Maximum two trades per day
- No order execution, no exchange trading keys, no auto-trading.
- 20x leverage is not a risk control; position size must be calculated from stop distance.

These are conservative configuration defaults, not a guarantee of safety or profitability. Signals are heuristic and require backtesting and paper trading before any live use.

## API
- `/health` — service health
- `/futures/scan` — scan all eligible Binance USD-M perpetuals; `?notify=true` enables Telegram alerts
- `/futures/telegram/test` — send a Telegram test message
- Existing research endpoints remain available: `/scan`, `/coin/{symbol}`, `/v3/coin/{symbol}`, `/providers`, `/ai/status`

## Deployment
Render configuration remains in `render.yaml`. Set Telegram environment variables in the Render service dashboard to enable Telegram delivery.
