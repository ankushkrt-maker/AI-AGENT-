import pandas as pd

def simple_reversal_backtest(df: pd.DataFrame, fee_bps=4, slippage_bps=2, hold_bars=6):
    x = df.copy().reset_index(drop=True)
    trades = []
    equity = 1.0
    peak = equity
    max_dd = 0.0
    for i in range(50, len(x)-hold_bars):
        low = x.loc[i,"low"]
        prev_low = x.loc[i-20:i-1,"low"].min()
        if low < prev_low and x.loc[i,"close"] > prev_low:
            entry = x.loc[i,"close"] * (1 + slippage_bps/10000)
            exitp = x.loc[i+hold_bars,"close"] * (1 - slippage_bps/10000)
            gross = exitp/entry - 1
            net = gross - 2*fee_bps/10000
            equity *= (1+net)
            peak = max(peak, equity)
            max_dd = max(max_dd, 1-equity/peak)
            trades.append(net)
    wins = sum(t>0 for t in trades)
    return {"trades": len(trades), "win_rate": wins/len(trades) if trades else 0, "total_return": equity-1, "max_drawdown": max_dd}
