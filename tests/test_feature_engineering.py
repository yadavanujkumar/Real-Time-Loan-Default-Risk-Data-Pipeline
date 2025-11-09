"""
Tests for feature engineering module
"""
import pytest
import pandas as pd
import numpy as np
from src.processing.feature_engineering import RiskFeatureEngineer


@pytest.fixture
def sample_data():
    """Create sample loan data for testing"""
    return pd.DataFrame({
        'customer_id': ['cust_1', 'cust_2', 'cust_3'],
        'loan_amount': [10000, 20000, 15000],
        'annual_income': [50000, 80000, 60000],
        'debt_amount': [5000, 10000, 3000],
        'employment_length': [5, 10, 3],
        'credit_limit': [15000, 30000, 18000]
    })


@pytest.fixture
def feature_engineer():
    """Create feature engineer instance"""
    return RiskFeatureEngineer()


def test_debt_to_income_ratio(sample_data, feature_engineer):
    """Test debt-to-income ratio calculation"""
    result = feature_engineer.calculate_debt_to_income_ratio(sample_data)
    
    assert 'debt_to_income_ratio' in result.columns
    assert result['debt_to_income_ratio'].iloc[0] == pytest.approx(0.1, rel=1e-2)
    assert result['debt_to_income_ratio'].iloc[1] == pytest.approx(0.125, rel=1e-2)
    assert result['debt_to_income_ratio'].iloc[2] == pytest.approx(0.05, rel=1e-2)


def test_credit_utilization(sample_data, feature_engineer):
    """Test credit utilization calculation"""
    result = feature_engineer.calculate_credit_utilization(sample_data)
    
    assert 'credit_utilization' in result.columns
    assert result['credit_utilization'].iloc[0] == pytest.approx(0.333, rel=1e-2)
    assert result['credit_utilization'].iloc[1] == pytest.approx(0.333, rel=1e-2)
    assert result['credit_utilization'].iloc[2] == pytest.approx(0.167, rel=1e-2)


def test_income_stability_score(sample_data, feature_engineer):
    """Test income stability score calculation"""
    result = feature_engineer.calculate_income_stability_score(sample_data)
    
    assert 'income_stability_score' in result.columns
    assert result['income_stability_score'].iloc[0] == pytest.approx(0.5, rel=1e-2)
    assert result['income_stability_score'].iloc[1] == pytest.approx(1.0, rel=1e-2)
    assert result['income_stability_score'].iloc[2] == pytest.approx(0.3, rel=1e-2)


def test_risk_categories(sample_data, feature_engineer):
    """Test risk category assignment"""
    sample_data['default_probability'] = [0.1, 0.6, 0.8]
    result = feature_engineer.create_risk_categories(sample_data)
    
    assert 'risk_category' in result.columns
    assert result['risk_category'].iloc[0] == 'Low'
    assert result['risk_category'].iloc[1] == 'Medium'
    assert result['risk_category'].iloc[2] == 'Very High'


def test_create_all_features(sample_data, feature_engineer):
    """Test creating all features at once"""
    result = feature_engineer.create_all_features(sample_data)
    
    expected_columns = [
        'debt_to_income_ratio',
        'loan_to_value_ratio',
        'credit_utilization',
        'income_stability_score',
        'default_probability',
        'risk_category'
    ]
    
    for col in expected_columns:
        assert col in result.columns


def test_empty_dataframe(feature_engineer):
    """Test handling of empty DataFrame"""
    empty_df = pd.DataFrame()
    
    # Should handle gracefully without errors
    result = feature_engineer.calculate_debt_to_income_ratio(empty_df)
    assert result.empty


def test_missing_values(feature_engineer):
    """Test handling of missing values"""
    df_with_na = pd.DataFrame({
        'customer_id': ['cust_1', 'cust_2'],
        'loan_amount': [10000, np.nan],
        'annual_income': [50000, 60000],
        'debt_amount': [np.nan, 5000],
        'employment_length': [5, np.nan]
    })
    
    result = feature_engineer.create_all_features(df_with_na)
    
    # Should fill NaN values
    assert not result['debt_to_income_ratio'].isna().any()
    assert not result['income_stability_score'].isna().any()
