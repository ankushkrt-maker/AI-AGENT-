import pandas as pd
import numpy as np
from app.signals.v3 import build_v3_signal


def test_v3_returns_research_signal():
    n = 120
    close = np.linspace(100, 120, n) + np.sin(np.arange(n))
    df = pd.DataFrame({
        "open": close - 0.2,
        "high": close + 0.5,
        "low": close - 0.5,
        "close": close,
        "volume": np.full(n, 1000.0),
    })
    result = build_v3_signal(df)
    assert result["decision"] in {"LONG", "SHORT", "NO TRADE"}
    assert 0 <= result["confidence"] <= 100
    assert result["mode"] == "research"
