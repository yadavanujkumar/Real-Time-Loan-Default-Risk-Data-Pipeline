"""
ML model training and prediction for loan default risk
"""
import os
import pickle
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)
from sklearn.preprocessing import StandardScaler
import mlflow
import mlflow.sklearn

from ..utils.config_loader import config
from ..utils.logger import setup_logger


logger = setup_logger(__name__)


class LoanDefaultModel:
    """ML model for predicting loan default risk"""
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        Initialize model
        
        Args:
            model_type: Type of model ('random_forest', 'gradient_boosting', 'logistic')
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        
        # Initialize MLflow
        mlflow_config = config.mlflow_config
        mlflow.set_tracking_uri(mlflow_config.get('tracking_uri'))
        mlflow.set_experiment(mlflow_config.get('experiment_name'))
        
        logger.info(f"Initialized {model_type} model")
    
    def _get_model(self):
        """Get model instance based on type"""
        if self.model_type == 'random_forest':
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'gradient_boosting':
            return GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        elif self.model_type == 'logistic':
            return LogisticRegression(
                max_iter=1000,
                random_state=42,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def prepare_features(
        self,
        df: pd.DataFrame,
        target_col: str = 'default',
        feature_cols: List[str] = None
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features for training
        
        Args:
            df: Input DataFrame
            target_col: Target column name
            feature_cols: List of feature columns (if None, auto-select)
            
        Returns:
            Tuple of (features, target)
        """
        if feature_cols is None:
            # Auto-select numeric columns excluding target
            feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if target_col in feature_cols:
                feature_cols.remove(target_col)
        
        self.feature_columns = feature_cols
        
        X = df[feature_cols].fillna(0)
        y = df[target_col] if target_col in df.columns else None
        
        logger.info(f"Prepared {len(feature_cols)} features for {len(X)} samples")
        return X, y
    
    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        scale_features: bool = True
    ) -> Dict[str, float]:
        """
        Train the model
        
        Args:
            X: Feature DataFrame
            y: Target Series
            test_size: Test set size
            scale_features: Whether to scale features
            
        Returns:
            Dictionary of evaluation metrics
        """
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Scale features
        if scale_features:
            X_train = pd.DataFrame(
                self.scaler.fit_transform(X_train),
                columns=X_train.columns,
                index=X_train.index
            )
            X_test = pd.DataFrame(
                self.scaler.transform(X_test),
                columns=X_test.columns,
                index=X_test.index
            )
        
        # Start MLflow run
        with mlflow.start_run():
            # Train model
            self.model = self._get_model()
            self.model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = self.model.predict(X_test)
            y_pred_proba = self.model.predict_proba(X_test)[:, 1]
            
            # Calculate metrics
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred),
                'f1_score': f1_score(y_test, y_pred),
                'roc_auc': roc_auc_score(y_test, y_pred_proba)
            }
            
            # Log to MLflow
            mlflow.log_params({
                'model_type': self.model_type,
                'n_features': len(self.feature_columns),
                'test_size': test_size,
                'scale_features': scale_features
            })
            mlflow.log_metrics(metrics)
            mlflow.sklearn.log_model(self.model, "model")
            
            logger.info(f"Model trained with metrics: {metrics}")
        
        return metrics
    
    def predict(self, X: pd.DataFrame, scale_features: bool = True) -> np.ndarray:
        """
        Make predictions
        
        Args:
            X: Feature DataFrame
            scale_features: Whether to scale features
            
        Returns:
            Predictions array
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Ensure correct columns
        X = X[self.feature_columns].fillna(0)
        
        # Scale if needed
        if scale_features:
            X = pd.DataFrame(
                self.scaler.transform(X),
                columns=X.columns,
                index=X.index
            )
        
        predictions = self.model.predict(X)
        logger.info(f"Made predictions for {len(X)} samples")
        return predictions
    
    def predict_proba(
        self,
        X: pd.DataFrame,
        scale_features: bool = True
    ) -> np.ndarray:
        """
        Predict probabilities
        
        Args:
            X: Feature DataFrame
            scale_features: Whether to scale features
            
        Returns:
            Probability array
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Ensure correct columns
        X = X[self.feature_columns].fillna(0)
        
        # Scale if needed
        if scale_features:
            X = pd.DataFrame(
                self.scaler.transform(X),
                columns=X.columns,
                index=X.index
            )
        
        probabilities = self.model.predict_proba(X)[:, 1]
        logger.info(f"Predicted probabilities for {len(X)} samples")
        return probabilities
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance (for tree-based models)
        
        Returns:
            DataFrame with feature importance
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        if hasattr(self.model, 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            logger.info("Retrieved feature importance")
            return importance_df
        else:
            logger.warning("Model does not support feature importance")
            return pd.DataFrame()
    
    def save_model(self, filepath: str):
        """
        Save model to disk
        
        Args:
            filepath: Path to save model
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'model_type': self.model_type
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """
        Load model from disk
        
        Args:
            filepath: Path to model file
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_columns = model_data['feature_columns']
        self.model_type = model_data['model_type']
        
        logger.info(f"Model loaded from {filepath}")
    
    def register_model(self, model_name: str):
        """
        Register model in MLflow model registry
        
        Args:
            model_name: Name for the registered model
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        with mlflow.start_run():
            mlflow.sklearn.log_model(
                self.model,
                "model",
                registered_model_name=model_name
            )
        
        logger.info(f"Model registered as {model_name}")
