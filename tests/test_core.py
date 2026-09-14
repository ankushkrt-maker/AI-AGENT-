from app.features.engine import add_features
from app.signals.scorer import scores, label
import pandas as pd


def sample_df(n=100):
    close = pd.Series([100 + i * 0.05 for i in range(n)])
    return pd.DataFrame({
        'open_time': pd.date_range('2026-01-01', periods=n, freq='5min', tz='UTC'),
        'open': close,
        'high': close + 1,
        'low': close - 1,
        'close': close,
        'volume': [1000.0] * n,
        'quote_volume': [100000.0] * n,
        'trades': [100] * n,
        'taker_buy_base': [500.0] * n,
        'taker_buy_quote': [50000.0] * n,
    })


def test_features_and_scores():
    df = add_features(sample_df())
    assert 'rvol' in df.columns
    latest = df.iloc[-1]
    features = {k: 0.0 if pd.isna(latest[k]) else float(latest[k]) for k in [
        'close','ret_1','ret_5','atr','atr_pct','rvol','vol_z','flow_delta','flow_z',
        'compression','sweep_low','sweep_high','bull_structure','bear_structure']}
    result = scores(features)
    assert set(result) == {'pre_pump','bottom','fakeout','exit_risk'}
    assert all(0 <= v <= 100 for v in result.values())
    assert label(85) == 'STRONG'
