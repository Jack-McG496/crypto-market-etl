import pandas as pd
from src.analytics.regime_detection import classify_volatility_regime

def test_high_regime_detection():
    df = pd.DataFrame({
        "z_score":[2.1],
        "threshold":[3]
    })

    result = classify_volatility_regime(df)

    assert result.iloc[0]["volatility_regime"] == "High"