import httpx
import pandas as pd
from app.config import BINANCE_BASE_URL, BINANCE_FALLBACK_URL


def _headers():
    return {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


async def _get_json(path: str, params: dict):
    urls = [f"{BINANCE_BASE_URL}{path}"]
    if BINANCE_FALLBACK_URL and BINANCE_FALLBACK_URL != BINANCE_BASE_URL:
        urls.append(f"{BINANCE_FALLBACK_URL}{path}")

    last_error = None
    async with httpx.AsyncClient(timeout=15, headers=_headers()) as client:
        for url in urls:
            try:
                r = await client.get(url, params=params)
                r.raise_for_status()
                return r.json()
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code not in (418, 429, 451, 500, 502, 503, 504):
                    raise
            except httpx.RequestError as e:
                last_error = e

    raise last_error or RuntimeError("Binance API request failed")


async def klines(symbol: str, interval: str = "5m", limit: int = 300) -> pd.DataFrame:
    data = await _get_json(
        "/fapi/v1/klines",
        {"symbol": symbol.upper(), "interval": interval, "limit": limit},
    )

    # If Binance Futures rejects the Render/cloud IP, retry against Binance Spot.
    # Spot candles keep the research/scoring dashboard functional.
    if not isinstance(data, list):
        data = await _get_json(
            "/api/v3/klines",
            {"symbol": symbol.upper(), "interval": interval, "limit": limit},
        )

    cols = ["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_buy_base","taker_buy_quote","ignore"]
    df = pd.DataFrame(data, columns=cols)
    for c in ["open","high","low","close","volume","quote_volume","taker_buy_base","taker_buy_quote"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df


async def ticker_24h():
    try:
        return await _get_json("/fapi/v1/ticker/24hr", {})
    except Exception:
        # Fallback to Spot 24h ticker when Futures API returns 418/geo/cloud rejection.
        return await _get_json("/api/v3/ticker/24hr", {})
