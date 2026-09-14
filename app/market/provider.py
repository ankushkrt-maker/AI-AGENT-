import httpx
import pandas as pd

BINANCE = "https://api.binance.com"
BYBIT = "https://api.bybit.com"

COLS = ["open_time", "open", "high", "low", "close", "volume", "quote_volume", "trades", "taker_buy_base", "taker_buy_quote"]


def _frame(rows):
    df = pd.DataFrame(rows, columns=COLS)
    for c in COLS[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df.dropna(subset=["open", "high", "low", "close", "volume"])


async def _get(client, url, params):
    r = await client.get(url, params=params)
    r.raise_for_status()
    return r.json()


async def klines(symbol: str, interval: str = "5m", limit: int = 200):
    symbol = symbol.upper()
    errors = []
    async with httpx.AsyncClient(timeout=12, headers={"User-Agent": "LiquidityHunterAI/2.0"}) as client:
        try:
            data = await _get(client, f"{BINANCE}/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit})
            rows = [[r[0], r[1], r[2], r[3], r[4], r[5], r[7], r[8], r[9], r[10]] for r in data]
            return _frame(rows), "binance_spot"
        except Exception as e:
            errors.append(f"binance: {e}")
        try:
            # Bybit linear candles: [start, open, high, low, close, volume, turnover]
            data = await _get(client, f"{BYBIT}/v5/market/kline", {"category": "linear", "symbol": symbol, "interval": _bybit_interval(interval), "limit": min(limit, 1000)})
            if data.get("retCode") != 0:
                raise RuntimeError(data.get("retMsg", "Bybit error"))
            raw = list(reversed(data["result"]["list"]))
            rows = [[r[0], r[1], r[2], r[3], r[4], r[5], r[6], 0, 0, 0] for r in raw]
            return _frame(rows), "bybit_linear"
        except Exception as e:
            errors.append(f"bybit: {e}")
    raise RuntimeError("All market data providers failed: " + " | ".join(errors))


def _bybit_interval(interval):
    mapping = {"1m": "1", "3m": "3", "5m": "5", "15m": "15", "30m": "30", "1h": "60", "2h": "120", "4h": "240", "6h": "360", "12h": "720", "1d": "D"}
    return mapping.get(interval, "5")


async def ticker_24h():
    async with httpx.AsyncClient(timeout=12, headers={"User-Agent": "LiquidityHunterAI/2.0"}) as client:
        try:
            data = await _get(client, f"{BINANCE}/api/v3/ticker/24hr", {})
            return data, "binance_spot"
        except Exception:
            data = await _get(client, f"{BYBIT}/v5/market/tickers", {"category": "linear"})
            if data.get("retCode") != 0:
                raise RuntimeError(data.get("retMsg", "Bybit ticker error"))
            rows = []
            for x in data["result"]["list"]:
                rows.append({"symbol": x.get("symbol", ""), "lastPrice": x.get("lastPrice", 0), "quoteVolume": x.get("turnover24h", 0), "priceChangePercent": x.get("price24hPcnt", 0)})
            return rows, "bybit_linear"
