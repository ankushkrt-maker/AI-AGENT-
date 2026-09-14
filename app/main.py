from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from app.config import APP_NAME, DEFAULT_SYMBOLS, DEFAULT_INTERVAL
from app.market.binance import klines, ticker_24h
from app.features.engine import latest_features
from app.signals.scorer import scores, label
from app.risk.engine import dynamic_stop
from app.ai.explainer import explain, llm_status

app = FastAPI(title=APP_NAME)

@app.get("/health")
async def health(): return {"ok": True, "app": APP_NAME}

@app.get("/scan")
async def scan(interval: str = DEFAULT_INTERVAL, limit: int = 30):
    tickers = await ticker_24h()
    candidates = [t for t in tickers if t.get("symbol","").endswith("USDT")]
    candidates.sort(key=lambda t: float(t.get("quoteVolume",0) or 0), reverse=True)
    wanted = list(DEFAULT_SYMBOLS)
    symbols = wanted + [t["symbol"] for t in candidates if t["symbol"] not in wanted][:max(0,limit-len(wanted))]
    rows=[]
    for symbol in symbols:
        try:
            f=latest_features(await klines(symbol,interval,200)); s=scores(f); best_name=max(s,key=s.get)
            rows.append({"symbol":symbol,**s,"best_signal":best_name,"score":s[best_name],"label":label(s[best_name])})
        except Exception as e: rows.append({"symbol":symbol,"error":str(e)})
    rows.sort(key=lambda r:r.get("score",0),reverse=True)
    return {"interval":interval,"results":rows}

@app.get("/coin/{symbol}")
async def coin(symbol: str, interval: str = DEFAULT_INTERVAL, limit: int = 300):
    try: df=await klines(symbol,interval,limit)
    except Exception as e: raise HTTPException(502,str(e))
    f=latest_features(df); s=scores(f); entry=f["close"]
    return {"symbol":symbol.upper(),"interval":interval,"features":f,"scores":s,"labels":{k:label(v) for k,v in s.items()},"risk_example":{"entry":entry,"long_stop":dynamic_stop(entry,f["atr"],"long")},"ai":explain(symbol.upper(),s,f)}

@app.get("/ai/status")
async def ai_status(): return llm_status()

@app.get("/", response_class=HTMLResponse)
async def home(): return open("frontend/index.html",encoding="utf-8").read()
