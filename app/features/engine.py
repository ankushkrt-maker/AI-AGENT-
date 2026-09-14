import numpy as np
import pandas as pd

def atr(df, n=14):
    prev = df["close"].shift(1)
    tr = pd.concat([df["high"]-df["low"], (df["high"]-prev).abs(), (df["low"]-prev).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x["ret_1"] = x["close"].pct_change()
    x["ret_5"] = x["close"].pct_change(5)
    x["atr"] = atr(x)
    x["atr_pct"] = x["atr"] / x["close"]
    x["vol_ma20"] = x["volume"].rolling(20).mean()
    x["rvol"] = x["volume"] / x["vol_ma20"].replace(0, np.nan)
    x["vol_z"] = (x["volume"]-x["volume"].rolling(50).mean()) / x["volume"].rolling(50).std()
    x["ema20"] = x["close"].ewm(span=20, adjust=False).mean()
    x["ema50"] = x["close"].ewm(span=50, adjust=False).mean()
    x["range20_high"] = x["high"].rolling(20).max().shift(1)
    x["range20_low"] = x["low"].rolling(20).min().shift(1)
    x["flow_delta"] = 2*x["taker_buy_base"] - x["volume"]
    x["flow_z"] = (x["flow_delta"]-x["flow_delta"].rolling(50).mean()) / x["flow_delta"].rolling(50).std()
    x["compression"] = x["atr_pct"] / x["atr_pct"].rolling(50).mean()
    x["sweep_low"] = (x["low"] < x["range20_low"]) & (x["close"] > x["range20_low"])
    x["sweep_high"] = (x["high"] > x["range20_high"]) & (x["close"] < x["range20_high"])
    x["bull_structure"] = (x["close"] > x["ema20"]) & (x["ema20"] > x["ema50"])
    x["bear_structure"] = (x["close"] < x["ema20"]) & (x["ema20"] < x["ema50"])
    return x.replace([np.inf, -np.inf], np.nan)

def latest_features(df):
    x = add_features(df).iloc[-1]
    def f(k, default=0.0):
        v = x.get(k, default)
        return default if pd.isna(v) else float(v)
    return {k: f(k) for k in ["close","ret_1","ret_5","atr","atr_pct","rvol","vol_z","flow_delta","flow_z","compression","sweep_low","sweep_high","bull_structure","bear_structure"]}
