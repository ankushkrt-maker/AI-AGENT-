from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from app.config import APP_NAME, DEFAULT_SYMBOLS, DEFAULT_INTERVAL
from app.market.provider import klines, ticker_24h
from app.features.engine import latest_features
from app.signals.scorer import scores, label
from app.signals.v3 import build_v3_signal
from app.risk.engine import dynamic_stop
from app.ai.explainer import explain, llm_status

app = FastAPI(title=APP_NAME, version="3.0")

@app.get("/health")
async def health():
    return {"ok": True, "app": APP_NAME, "version": "3.0", "mode": "research"}

@app.get("/providers")
async def providers():
    try:
        _, provider = await ticker_24h()
        return {"ok": True, "active_provider": provider, "fallback": "bybit_linear" if provider == "binance_spot" else "binance_spot"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/scan")
async def scan(interval: str = DEFAULT_INTERVAL, limit: int = 30):
    tickers, provider = await ticker_24h()
    candidates = [t for t in tickers if t.get("symbol", "").endswith("USDT")]
    candidates.sort(key=lambda t: float(t.get("quoteVolume", 0) or 0), reverse=True)
    wanted = list(DEFAULT_SYMBOLS)
    symbols = wanted + [t["symbol"] for t in candidates if t["symbol"] not in wanted][:max(0, limit-len(wanted))]
    rows = []
    for symbol in symbols:
        try:
            df, candle_provider = await klines(symbol, interval, 200)
            f = latest_features(df)
            s = scores(f)
            best_name = max(s, key=s.get)
            v3 = build_v3_signal(df)
            rows.append({"symbol": symbol, **s, "best_signal": best_name, "score": s[best_name], "label": label(s[best_name]), "v3_decision": v3["decision"], "v3_confidence": v3["confidence"], "data_provider": candle_provider})
        except Exception as e:
            rows.append({"symbol": symbol, "error": str(e), "data_provider": provider})
    rows.sort(key=lambda r: r.get("v3_confidence", r.get("score", 0)), reverse=True)
    return {"version": "3.0", "interval": interval, "ticker_provider": provider, "results": rows}

@app.get("/coin/{symbol}")
async def coin(symbol: str, interval: str = DEFAULT_INTERVAL, limit: int = 300):
    try:
        df, provider = await klines(symbol, interval, limit)
    except Exception as e:
        raise HTTPException(502, str(e))
    f = latest_features(df)
    s = scores(f)
    entry = f["close"]
    return {"version": "3.0", "symbol": symbol.upper(), "interval": interval, "data_provider": provider, "features": f, "scores": s, "labels": {k: label(v) for k, v in s.items()}, "v3": build_v3_signal(df), "risk_example": {"entry": entry, "long_stop": dynamic_stop(entry, f["atr"], "long")}, "ai": explain(symbol.upper(), s, f)}

@app.get("/v3/coin/{symbol}")
async def v3_coin(symbol: str, interval: str = DEFAULT_INTERVAL, limit: int = 300):
    try:
        df, provider = await klines(symbol, interval, limit)
        return {"version": "3.0", "symbol": symbol.upper(), "interval": interval, "data_provider": provider, "signal": build_v3_signal(df)}
    except Exception as e:
        raise HTTPException(502, str(e))

@app.get("/ai/status")
async def ai_status():
    return llm_status()

@app.get("/", response_class=HTMLResponse)
async def home():
    return open("frontend/pro.html", encoding="utf-8").read()
