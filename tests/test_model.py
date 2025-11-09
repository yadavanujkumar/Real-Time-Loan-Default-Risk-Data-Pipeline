"""
Tests for ML model
"""
import pytest
import pandas as pd
import numpy as np
from src.models.loan_default_model import LoanDefaultModel


@pytest.fixture
def sample_training_data():
    """Create sample training data"""
    np.random.seed(42)
    n_samples = 100
    
    return pd.DataFrame({
        'debt_to_income_ratio': np.random.uniform(0.1, 0.8, n_samples),
        'credit_utilization': np.random.uniform(0.1, 0.9, n_samples),
        'loan_to_value_ratio': np.random.uniform(0.2, 1.5, n_samples),
        'income_stability_score': np.random.uniform(0.3, 1.0, n_samples),
        'default': np.random.choice([0, 1], n_samples, p=[0.7, 0.3])
    })


def test_model_initialization():
    """Test model initialization"""
    model = LoanDefaultModel(model_type='random_forest')
    assert model.model_type == 'random_forest'
    assert model.model is None
    assert len(model.feature_columns) == 0


def test_prepare_features(sample_training_data):
    """Test feature preparation"""
    model = LoanDefaultModel()
    X, y = model.prepare_features(sample_training_data, target_col='default')
    
    assert len(X) == 100
    assert len(y) == 100
    assert 'default' not in X.columns
    assert len(model.feature_columns) > 0


def test_model_training(sample_training_data):
    """Test model training"""
    model = LoanDefaultModel(model_type='random_forest')
    X, y = model.prepare_features(sample_training_data, target_col='default')
    metrics = model.train(X, y, test_size=0.2)
    
    assert 'accuracy' in metrics
    assert 'precision' in metrics
    assert 'recall' in metrics
    assert 'f1_score' in metrics
    assert 'roc_auc' in metrics
    
    # Check that metrics are in valid range
    for metric_name, value in metrics.items():
        assert 0 <= value <= 1, f"{metric_name} should be between 0 and 1"


def test_model_prediction(sample_training_data):
    """Test model predictions"""
    model = LoanDefaultModel(model_type='random_forest')
    X, y = model.prepare_features(sample_training_data, target_col='default')
    model.train(X, y, test_size=0.2)
    
    # Make predictions on a subset
    predictions = model.predict(X.head(10))
    
    assert len(predictions) == 10
    assert all(pred in [0, 1] for pred in predictions)


def test_predict_proba(sample_training_data):
    """Test probability predictions"""
    model = LoanDefaultModel(model_type='random_forest')
    X, y = model.prepare_features(sample_training_data, target_col='default')
    model.train(X, y, test_size=0.2)
    
    probabilities = model.predict_proba(X.head(10))
    
    assert len(probabilities) == 10
    assert all(0 <= prob <= 1 for prob in probabilities)


def test_feature_importance(sample_training_data):
    """Test feature importance retrieval"""
    model = LoanDefaultModel(model_type='random_forest')
    X, y = model.prepare_features(sample_training_data, target_col='default')
    model.train(X, y, test_size=0.2)
    
    importance_df = model.get_feature_importance()
    
    assert not importance_df.empty
    assert 'feature' in importance_df.columns
    assert 'importance' in importance_df.columns


def test_model_save_load(sample_training_data, tmp_path):
    """Test model saving and loading"""
    model = LoanDefaultModel(model_type='random_forest')
    X, y = model.prepare_features(sample_training_data, target_col='default')
    model.train(X, y, test_size=0.2)
    
    # Save model
    model_path = tmp_path / "test_model.pkl"
    model.save_model(str(model_path))
    
    # Load model
    new_model = LoanDefaultModel()
    new_model.load_model(str(model_path))
    
    # Check that loaded model can make predictions
    predictions = new_model.predict(X.head(5))
    assert len(predictions) == 5


def test_different_model_types():
    """Test different model types"""
    model_types = ['random_forest', 'gradient_boosting', 'logistic']
    
    for model_type in model_types:
        model = LoanDefaultModel(model_type=model_type)
        assert model.model_type == model_type


def test_prediction_before_training():
    """Test that prediction fails before training"""
    model = LoanDefaultModel()
    
    with pytest.raises(ValueError):
        model.predict(pd.DataFrame({'feature1': [1, 2, 3]}))
