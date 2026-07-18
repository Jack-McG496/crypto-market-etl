import pandas as pd
from src.analytics.regime_detection import classify_volatility_regime

def test_calm_regime_detection():
    df = pd.DataFrame({
        "z_score":[0.1],
        "threshold":[1]
    })

    result = classify_volatility_regime(df)

    assert result.iloc[0]["volatility_regime"] == "Calm"

def test_elevated_regime_detection():
    df = pd.DataFrame({
        "z_score":[1.1],
        "threshold":[2]
    })

    result = classify_volatility_regime(df)

    assert result.iloc[0]["volatility_regime"] == "Elevated"

def test_high_regime_detection():
    df = pd.DataFrame({
        "z_score":[2.1],
        "threshold":[3]
    })

    result = classify_volatility_regime(df)

    assert result.iloc[0]["volatility_regime"] == "High"

def test_extreme_regime_detection():
    df = pd.DataFrame({
        "z_score":[3.1],
        "threshold":[3]
    })

    result = classify_volatility_regime(df)

    assert result.iloc[0]["volatility_regime"] == "Extreme"
