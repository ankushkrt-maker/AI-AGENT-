# LIQUIDITY HUNTER AI v2

Crypto market research and scalping-signal research dashboard.

## V2 architecture
- Multi-provider market data: Binance Spot primary, Bybit Linear fallback
- No dependency on Binance Futures `/fapi` endpoints
- Provider visibility via `/providers`
- Multiple timeframe candle mapping
- Existing quantitative features, heuristic scoring and risk helper
- Research/paper mode only; no live order execution

## API
- `/health` — service health
- `/providers` — active data provider and fallback
- `/scan?interval=5m&limit=30` — ranked market scan
- `/coin/BTCUSDT?interval=5m` — detailed symbol analysis
- `/ai/status` — AI integration status

## Deployment
Designed for Render with the existing `render.yaml` configuration.
