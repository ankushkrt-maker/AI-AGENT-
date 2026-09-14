def clamp(v): return max(0.0, min(100.0, float(v)))

def scores(f):
    pre = 0
    pre += 15 if f["rvol"] >= 1.5 else 8 if f["rvol"] >= 1.1 else 0
    pre += 10 if f["vol_z"] >= 1 else 0
    pre += 10 if f["flow_z"] > 0.8 else 5 if f["flow_z"] > 0 else 0
    pre += 15 if f["compression"] < 0.8 else 8 if f["compression"] < 1 else 0
    pre += 15 if f["sweep_low"] else 0
    pre += 15 if f["bull_structure"] else 0
    pre += 10 if f["ret_5"] > 0 else 0
    pre += 10 if f["atr_pct"] > 0 else 0
    bottom = 0
    bottom += 20 if f["sweep_low"] else 0
    bottom += 15 if f["flow_z"] > 0.5 else 0
    bottom += 15 if f["rvol"] >= 1.5 else 0
    bottom += 15 if f["ret_1"] > 0 else 0
    bottom += 15 if f["close"] > 0 and not f["bear_structure"] else 0
    bottom += 10 if f["compression"] < 1 else 0
    bottom += 10 if f["vol_z"] > 0 else 0
    fakeout = 0
    fakeout += 30 if f["sweep_high"] else 0
    fakeout += 20 if f["vol_z"] < 0.5 else 0
    fakeout += 20 if f["flow_z"] < 0 else 0
    fakeout += 15 if f["bear_structure"] else 0
    fakeout += 15 if f["ret_1"] < 0 else 0
    exit_score = 0
    exit_score += 30 if f["sweep_high"] else 0
    exit_score += 20 if f["flow_z"] < -0.8 else 0
    exit_score += 20 if f["bear_structure"] else 0
    exit_score += 15 if f["vol_z"] > 2 else 0
    exit_score += 15 if f["ret_1"] < 0 else 0
    return {"pre_pump":clamp(pre),"bottom":clamp(bottom),"fakeout":clamp(fakeout),"exit_risk":clamp(exit_score)}

def label(score):
    if score >= 90: return "EXTREME"
    if score >= 80: return "STRONG"
    if score >= 70: return "GOOD"
    if score >= 60: return "WEAK"
    if score >= 40: return "WATCH"
    return "NO TRADE"
