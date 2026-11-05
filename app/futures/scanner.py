import asyncio
import os
from datetime import datetime, timezone

import httpx
import pandas as pd

BASE = "https://fapi.binance.com"
TIMEFRAME = os.getenv("FUTURES_SCAN_INTERVAL", "5m")
MIN_QUOTE_VOLUME = float(os.getenv("MIN_QUOTE_VOLUME_USDT", "5000000"))
MAX_CONCURRENCY = int(os.getenv("SCAN_CONCURRENCY", "6"))
ACCOUNT_INR = float(os.getenv("ACCOUNT_EQUITY_INR", "10000"))
RISK_PCT = float(os.getenv("MAX_RISK_PER_TRADE_PCT", "0.25"))
MAX_DAILY_LOSS_PCT = float(os.getenv("MAX_DAILY_LOSS_PCT", "0.5"))


async def _json(client, path, params=None):
    r = await client.get(BASE + path, params=params)
    r.raise_for_status()
    return r.json()


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


async def _symbol_scan(client, sem, symbol, ticker, funding):
    async with sem:
        try:
            raw, oi = await asyncio.gather(
                _json(client, "/fapi/v1/klines", {"symbol": symbol, "interval": TIMEFRAME, "limit": 100}),
                _json(client, "/futures/data/openInterestHist", {"symbol": symbol, "period": TIMEFRAME, "limit": 3}),
            )
            # Use completed candles only; the final kline is still forming.
            if len(raw) < 65:
                return None
            rows = raw[:-1]
            df = pd.DataFrame(rows, columns=["t","o","h","l","c","v","ct","qv","n","tbv","tbq","x"])
            for col in ["o","h","l","c","v","qv","tbv"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            if len(oi) < 2:
                return {"symbol": symbol, "decision": "NO TRADE", "reason": "OI history unavailable", "quote_volume": _num(ticker.get("quoteVolume"))}
            oi_now = _num(oi[-1].get("sumOpenInterestValue"))
            oi_prev = _num(oi[-2].get("sumOpenInterestValue"))
            oi_change = ((oi_now / oi_prev) - 1) * 100 if oi_prev else 0.0

            last = df.iloc[-1]
            prev = df.iloc[-2]
            recent = df.iloc[-21:-1]
            high20 = recent["h"].max()
            low20 = recent["l"].min()
            close = _num(last["c"])
            op = _num(last["o"])
            high = _num(last["h"])
            low = _num(last["l"])
            volume = _num(last["v"])
            avg_vol = _num(df["v"].iloc[-21:-1].mean())
            rvol = volume / avg_vol if avg_vol else 0.0
            taker_ratio = _num(last["tbv"]) / volume if volume else 0.5
            ema20 = _num(df["c"].ewm(span=20, adjust=False).mean().iloc[-1])
            ema50 = _num(df["c"].ewm(span=50, adjust=False).mean().iloc[-1])
            tr = pd.concat([df["h"]-df["l"], (df["h"]-df["c"].shift()).abs(), (df["l"]-df["c"].shift()).abs()], axis=1).max(axis=1)
            atr = _num(tr.rolling(14).mean().iloc[-1])
            sweep_low = low < low20 and close > low20
            sweep_high = high > high20 and close < high20
            bull_break = close > _num(df["h"].iloc[-11:-1].max())
            bear_break = close < _num(df["l"].iloc[-11:-1].min())
            body = abs(close-op)
            bull_displacement = close > op and atr > 0 and body >= 0.8*atr
            bear_displacement = close < op and atr > 0 and body >= 0.8*atr
            bull_fvg = low > _num(df["h"].iloc[-3])
            bear_fvg = high < _num(df["l"].iloc[-3])
            bull_bias = close > ema20 > ema50
            bear_bias = close < ema20 < ema50
            oi_up = oi_change > 0.5
            oi_down = oi_change < -0.5
            fund = _num(funding.get(symbol, {}).get("lastFundingRate")) * 100

            long_score = 0
            short_score = 0
            long_reasons, short_reasons = [], []
            def add(condition, side, points, reason):
                nonlocal long_score, short_score
                if condition:
                    if side == "LONG":
                        long_score += points
                        long_reasons.append(reason)
                    else:
                        short_score += points
                        short_reasons.append(reason)

            add(bull_bias, "LONG", 15, "EMA20 > EMA50 bullish bias")
            add(bear_bias, "SHORT", 15, "EMA20 < EMA50 bearish bias")
            add(sweep_low, "LONG", 20, "Sell-side liquidity sweep")
            add(sweep_high, "SHORT", 20, "Buy-side liquidity sweep")
            add(bull_displacement, "LONG", 15, "Bullish displacement")
            add(bear_displacement, "SHORT", 15, "Bearish displacement")
            add(bull_break, "LONG", 15, "Bullish MSS / structure break")
            add(bear_break, "SHORT", 15, "Bearish MSS / structure break")
            add(bull_fvg, "LONG", 5, "Bullish FVG")
            add(bear_fvg, "SHORT", 5, "Bearish FVG")
            add(rvol >= 1.5, "LONG" if taker_ratio >= 0.55 else "SHORT", 10, "Relative volume >= 1.5x with taker flow")
            add(oi_up, "LONG" if taker_ratio >= 0.55 else "SHORT", 10, "Open interest rising with directional taker flow")
            # OI contraction is context, not a directional entry trigger.
            if oi_down:
                long_reasons.append("OI contracting: possible position unwind")
                short_reasons.append("OI contracting: possible position unwind")

            edge = long_score - short_score
            if max(long_score, short_score) < 65 or abs(edge) < 20 or not (oi_up and rvol >= 1.2):
                decision = "NO TRADE"
            else:
                decision = "LONG" if long_score > short_score else "SHORT"
            stop_distance = max(atr * 1.5, close * 0.002)
            stop = close - stop_distance if decision == "LONG" else close + stop_distance if decision == "SHORT" else None
            risk_inr = ACCOUNT_INR * RISK_PCT / 100
            return {
                "symbol": symbol, "decision": decision, "long_score": min(long_score,100),
                "short_score": min(short_score,100), "confidence": max(long_score,short_score),
                "price": close, "rvol": round(rvol,2), "oi_change_pct": round(oi_change,2),
                "taker_buy_ratio": round(taker_ratio,3), "funding_pct": round(fund,4),
                "sweep_low": bool(sweep_low), "sweep_high": bool(sweep_high),
                "displacement": "bullish" if bull_displacement else "bearish" if bear_displacement else "none",
                "structure_break": "bullish" if bull_break else "bearish" if bear_break else "none",
                "stop": stop, "risk_budget_inr": round(risk_inr,2),
                "quote_volume": _num(ticker.get("quoteVolume")),
                "reasons": long_reasons if decision == "LONG" else short_reasons if decision == "SHORT" else {"long":long_reasons,"short":short_reasons},
                "closed_candle_only": True,
            }
        except Exception as exc:
            return {"symbol": symbol, "decision": "NO TRADE", "reason": str(exc)[:180]}


async def scan_all_futures():
    timeout = httpx.Timeout(15.0, connect=8.0)
    async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent":"LiquidityHunterAI/4.0"}) as client:
        exchange, tickers, premiums = await asyncio.gather(
            _json(client, "/fapi/v1/exchangeInfo"),
            _json(client, "/fapi/v1/ticker/24hr"),
            _json(client, "/fapi/v1/premiumIndex"),
        )
        active = {s["symbol"] for s in exchange.get("symbols", [])
                  if s.get("status") == "TRADING" and s.get("contractType") == "PERPETUAL"
                  and s.get("quoteAsset") == "USDT"}
        ticker_map = {t["symbol"]: t for t in tickers if t.get("symbol") in active}
        funding_map = {p["symbol"]: p for p in premiums}
        liquid = [s for s in active if _num(ticker_map.get(s, {}).get("quoteVolume")) >= MIN_QUOTE_VOLUME]
        liquid.sort(key=lambda s: _num(ticker_map[s].get("quoteVolume")), reverse=True)
        sem = asyncio.Semaphore(MAX_CONCURRENCY)
        tasks = [_symbol_scan(client, sem, s, ticker_map[s], funding_map) for s in liquid]
        results = await asyncio.gather(*tasks)
        rows = [x for x in results if x]
        rows.sort(key=lambda x: (x.get("decision") != "NO TRADE", x.get("confidence",0), x.get("quote_volume",0)), reverse=True)
        signals = [x for x in rows if x.get("decision") in ("LONG","SHORT")]
        return {
            "universe": "Binance USD-M USDT perpetuals",
            "active_contracts": len(active),
            "liquid_contracts_scanned": len(liquid),
            "min_quote_volume_usdt": MIN_QUOTE_VOLUME,
            "interval": TIMEFRAME,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "signal-only / research",
            "risk": {"account_equity_inr": ACCOUNT_INR, "risk_per_trade_pct": RISK_PCT,
                     "risk_per_trade_inr": round(ACCOUNT_INR*RISK_PCT/100,2),
                     "daily_loss_limit_pct": MAX_DAILY_LOSS_PCT,
                     "max_trades_per_day": 2, "leverage_note": "20x is not a risk control; size from stop distance."},
            "signals": len(signals),
            "results": rows,
        }
