# Google AI Studio Build Prompt

Build on this repository and implement the roadmap in `docs/ROADMAP.md`.

Product: LIQUIDITY HUNTER AI.

Requirements:
- Preserve the existing working Phase 1.
- Do not fabricate market/OI/liquidation/order-book data.
- Use provider adapters for Binance, Bybit and future derivatives providers.
- Implement true WebSocket ingestion, OI, funding, liquidations, trade-level CVD, order-book imbalance/absorption, multi-timeframe SMC/ICT, pre-pump, liquidity-hunt, fakeout, whale-eye and pre-dump engines.
- Add PostgreSQL/TimescaleDB + Redis when persistent/realtime infrastructure is introduced.
- Add trade journal, paper trading, realistic backtesting, 1000+ trade validation harness, walk-forward and out-of-sample testing.
- Add champion/challenger strategy versioning and rollback.
- Add Telegram alerts.
- Keep live execution disabled by default and behind explicit configuration and hard risk limits.
- Never claim guaranteed profit or 85% accuracy.
- Never use future data, look-ahead bias, survivorship bias or fake results.
- Keep secrets out of source control.
- Keep deterministic market calculations in Python; use an LLM only for explanations, ranking, research and experiment proposals.
- Build mobile-first PWA UI.

Implement one phase at a time. After each phase:
1. list changed files
2. run tests
3. explain what works
4. list limitations
5. do not silently invent unavailable data.
