from src.analytics.volatility_analysis import calculate_volatility_features

def test_returns_are_computed(sample_market_df):

    result = calculate_volatility_features(
        sample_market_df,
        window=10
    )

    assert "returns" in result.columns

def test_rolling_std_computed(sample_market_df):

    result = calculate_volatility_features(
        sample_market_df,
        window=10
    )

    assert "rolling_std" in result.columns

def test_z_score_computed(sample_market_df):

    result = calculate_volatility_features(
        sample_market_df,
        window=10
    )

    assert "z_score" in result.columns