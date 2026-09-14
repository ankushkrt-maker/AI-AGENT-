import httpx
import pandas as pd
from app.config import BINANCE_BASE_URL

BINANCE_SPOT_URL = "https://api.binance.com"


def _headers():
    return {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


async def _get_json(url: str, params: dict):
    last_error = None
    async with httpx.AsyncClient(timeout=15, headers=_headers()) as client:
        try:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            last_error = e
        except httpx.RequestError as e:
            last_error = e
    raise last_error or RuntimeError("Binance API request failed")


async def klines(symbol: str, interval: str = "5m", limit: int = 300) -> pd.DataFrame:
    # Use Binance Spot market data directly. It has the same OHLCV candle shape
    # needed by this research/scoring engine and avoids cloud-IP Futures 418 blocks.
    data = await _get_json(
        f"{BINANCE_SPOT_URL}/api/v3/klines",
        {"symbol": symbol.upper(), "interval": interval, "limit": limit},
    )

    cols = ["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_buy_base","taker_buy_quote","ignore"]
    df = pd.DataFrame(data, columns=cols)
    for c in ["open","high","low","close","volume","quote_volume","taker_buy_base","taker_buy_quote"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df


async def ticker_24h():
    # Spot 24h ticker is sufficient for the dashboard's market ranking.
    return await _get_json(f"{BINANCE_SPOT_URL}/api/v3/ticker/24hr", {})
