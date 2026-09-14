def position_size(account_equity: float, risk_pct: float, entry: float, stop: float):
    risk_cash = account_equity * (risk_pct/100.0)
    distance = abs(entry-stop)
    if distance <= 0: return 0.0
    return risk_cash / distance

def dynamic_stop(entry: float, atr_value: float, side="long", atr_mult=1.5):
    d = max(atr_value * atr_mult, entry * 0.002)
    return entry-d if side=="long" else entry+d
