from src.analytics.volatility_analysis import calculate_volatility_features
from tests.conftest import sample_market_df

def test_returns_are_computed():

    result = calculate_volatility_features(
        sample_market_df,
        window=10
    )

    # Assert result
    assert "returns" in result.columns

def test_rolling_std_computed():

    result = calculate_volatility_features(
        sample_market_df,
        window=10
    )

    assert "rolling_std" in result.columns

def test_z_score_computed():

    result = calculate_volatility_features(
        sample_market_df,
        window=10
    )

    assert "z_score" in result.columns