import httpx
from typing import Any

async def ticker(symbol: str) -> Any:
    url = "https://api.bybit.com/v5/market/tickers"
    params = {"category": "linear", "symbol": symbol.upper()}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()
