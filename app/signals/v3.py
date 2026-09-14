import numpy as np
import pandas as pd


def _bool(v):
    return bool(v) if not pd.isna(v) else False


def build_v3_signal(df: pd.DataFrame) -> dict:
    """Research-only multi-factor signal model. No execution logic."""
    if len(df) < 60:
        raise ValueError("At least 60 candles are required for V3 analysis")

    x = df.copy().reset_index(drop=True)
    close = pd.to_numeric(x["close"], errors="coerce")
    high = pd.to_numeric(x["high"], errors="coerce")
    low = pd.to_numeric(x["low"], errors="coerce")
    volume = pd.to_numeric(x["volume"], errors="coerce")

    x["ema20"] = close.ewm(span=20, adjust=False).mean()
    x["ema50"] = close.ewm(span=50, adjust=False).mean()
    x["vwap"] = (close * volume).cumsum() / volume.cumsum().replace(0, np.nan)
    x["atr"] = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1).rolling(14).mean()
    x["rvol"] = volume / volume.rolling(20).mean().replace(0, np.nan)
    x["range_high"] = high.rolling(20).max().shift(1)
    x["range_low"] = low.rolling(20).min().shift(1)

    # Liquidity sweeps: wick through a prior 20-candle extreme and close back inside.
    x["sweep_low"] = (low < x["range_low"]) & (close > x["range_low"])
    x["sweep_high"] = (high > x["range_high"]) & (close < x["range_high"])

    # Displacement: large body relative to ATR with directional close.
    body = (close - x["open"]).abs()
    x["bull_displacement"] = (close > x["open"]) & (body > x["atr"] * 0.8) & (x["rvol"] >= 1.2)
    x["bear_displacement"] = (close < x["open"]) & (body > x["atr"] * 0.8) & (x["rvol"] >= 1.2)

    # Three-candle fair-value-gap approximation.
    x["bull_fvg"] = low > high.shift(2)
    x["bear_fvg"] = high < low.shift(2)

    # Simple market-structure proxy using recent swing breaks.
    x["bull_break"] = close > high.rolling(10).max().shift(1)
    x["bear_break"] = close < low.rolling(10).min().shift(1)
    x["bull_bias"] = (close > x["ema20"]) & (x["ema20"] > x["ema50"]) & (close > x["vwap"])
    x["bear_bias"] = (close < x["ema20"]) & (x["ema20"] < x["ema50"]) & (close < x["vwap"])

    r = x.iloc[-1]
    long_points = 0
    short_points = 0
    long_reasons, short_reasons = [], []

    if _bool(r["bull_bias"]): long_points += 20; long_reasons.append("EMA20>EMA50 + price above VWAP")
    if _bool(r["bear_bias"]): short_points += 20; short_reasons.append("EMA20<EMA50 + price below VWAP")
    if _bool(r["sweep_low"]): long_points += 20; long_reasons.append("sell-side liquidity sweep")
    if _bool(r["sweep_high"]): short_points += 20; short_reasons.append("buy-side liquidity sweep")
    if _bool(r["bull_displacement"]): long_points += 15; long_reasons.append("bullish displacement")
    if _bool(r["bear_displacement"]): short_points += 15; short_reasons.append("bearish displacement")
    if _bool(r["bull_break"]): long_points += 15; long_reasons.append("bullish structure break")
    if _bool(r["bear_break"]): short_points += 15; short_reasons.append("bearish structure break")
    if _bool(r["bull_fvg"]): long_points += 10; long_reasons.append("bullish FVG")
    if _bool(r["bear_fvg"]): short_points += 10; short_reasons.append("bearish FVG")
    if float(r["rvol"] or 0) >= 1.5:
        long_points += 10 if long_points > short_points else 0
        short_points += 10 if short_points > long_points else 0

    long_score = min(100, long_points)
    short_score = min(100, short_points)
    edge = long_score - short_score
    if max(long_score, short_score) < 60 or abs(edge) < 15:
        decision = "NO TRADE"
    elif long_score > short_score:
        decision = "LONG"
    else:
        decision = "SHORT"

    atr_value = float(r["atr"]) if not pd.isna(r["atr"]) else 0.0
    entry = float(r["close"])
    stop_distance = atr_value * 1.5
    risk = {"entry": entry, "atr": atr_value, "stop_distance": stop_distance}
    if decision == "LONG":
        risk.update(stop=entry-stop_distance, target_1=entry+stop_distance*1.5, target_2=entry+stop_distance*2.5)
    elif decision == "SHORT":
        risk.update(stop=entry+stop_distance, target_1=entry-stop_distance*1.5, target_2=entry-stop_distance*2.5)
    else:
        risk.update(stop=None, target_1=None, target_2=None)

    return {
        "decision": decision,
        "long_score": long_score,
        "short_score": short_score,
        "confidence": max(long_score, short_score),
        "reasons": long_reasons if decision == "LONG" else short_reasons if decision == "SHORT" else {"long": long_reasons, "short": short_reasons},
        "market": {"close": entry, "ema20": float(r["ema20"]), "ema50": float(r["ema50"]), "vwap": float(r["vwap"]), "rvol": float(r["rvol"]) if not pd.isna(r["rvol"]) else 0.0},
        "structure": {"sweep_low": _bool(r["sweep_low"]), "sweep_high": _bool(r["sweep_high"]), "bull_displacement": _bool(r["bull_displacement"]), "bear_displacement": _bool(r["bear_displacement"]), "bull_fvg": _bool(r["bull_fvg"]), "bear_fvg": _bool(r["bear_fvg"]), "bull_break": _bool(r["bull_break"]), "bear_break": _bool(r["bear_break"])},
        "risk_example": risk,
        "mode": "research",
    }
