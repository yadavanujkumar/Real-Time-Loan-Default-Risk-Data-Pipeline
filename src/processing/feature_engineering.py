"""
Feature engineering for loan default risk prediction
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta

from ..utils.logger import setup_logger


logger = setup_logger(__name__)


class RiskFeatureEngineer:
    """Feature engineering for risk assessment"""
    
    def __init__(self):
        """Initialize feature engineer"""
        self.feature_columns = []
        logger.info("Risk feature engineer initialized")
    
    def calculate_debt_to_income_ratio(
        self,
        df: pd.DataFrame,
        debt_col: str = 'debt_amount',
        income_col: str = 'annual_income'
    ) -> pd.DataFrame:
        """
        Calculate debt-to-income ratio
        
        Args:
            df: Input DataFrame
            debt_col: Column name for debt amount
            income_col: Column name for income
            
        Returns:
            DataFrame with debt_to_income_ratio column
        """
        df['debt_to_income_ratio'] = (
            df[debt_col] / df[income_col]
        ).fillna(0)
        
        self.feature_columns.append('debt_to_income_ratio')
        logger.info("Calculated debt-to-income ratio")
        return df
    
    def calculate_loan_to_value_ratio(
        self,
        df: pd.DataFrame,
        loan_col: str = 'loan_amount',
        value_col: str = 'collateral_value'
    ) -> pd.DataFrame:
        """
        Calculate loan-to-value ratio
        
        Args:
            df: Input DataFrame
            loan_col: Column name for loan amount
            value_col: Column name for collateral value
            
        Returns:
            DataFrame with loan_to_value_ratio column
        """
        if value_col not in df.columns:
            # Use annual income as proxy for value
            value_col = 'annual_income'
        
        df['loan_to_value_ratio'] = (
            df[loan_col] / df[value_col]
        ).fillna(0)
        
        self.feature_columns.append('loan_to_value_ratio')
        logger.info("Calculated loan-to-value ratio")
        return df
    
    def calculate_credit_utilization(
        self,
        df: pd.DataFrame,
        debt_col: str = 'debt_amount',
        limit_col: str = 'credit_limit'
    ) -> pd.DataFrame:
        """
        Calculate credit utilization ratio
        
        Args:
            df: Input DataFrame
            debt_col: Column name for debt
            limit_col: Column name for credit limit
            
        Returns:
            DataFrame with credit_utilization column
        """
        if limit_col not in df.columns:
            # Estimate credit limit based on income
            df['credit_limit'] = df.get('annual_income', 0) * 0.3
        
        df['credit_utilization'] = (
            df[debt_col] / df['credit_limit']
        ).fillna(0)
        
        # Cap at 100%
        df['credit_utilization'] = df['credit_utilization'].clip(upper=1.0)
        
        self.feature_columns.append('credit_utilization')
        logger.info("Calculated credit utilization")
        return df
    
    def calculate_payment_history_features(
        self,
        df: pd.DataFrame,
        payment_history: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        Calculate payment history features
        
        Args:
            df: Input DataFrame with customer_id
            payment_history: DataFrame with payment records
            
        Returns:
            DataFrame with payment history features
        """
        if payment_history is None or payment_history.empty:
            df['avg_payment_delay_days'] = 0
            df['late_payment_count'] = 0
            df['late_payment_ratio'] = 0
            return df
        
        # Aggregate payment history by customer
        payment_agg = payment_history.groupby('customer_id').agg({
            'payment_delay_days': 'mean',
            'late_payment_indicator': ['sum', 'count']
        }).reset_index()
        
        payment_agg.columns = [
            'customer_id',
            'avg_payment_delay_days',
            'late_payment_count',
            'total_payments'
        ]
        
        payment_agg['late_payment_ratio'] = (
            payment_agg['late_payment_count'] / payment_agg['total_payments']
        )
        
        # Merge with main dataframe
        df = df.merge(payment_agg, on='customer_id', how='left')
        
        # Fill missing values
        df['avg_payment_delay_days'] = df['avg_payment_delay_days'].fillna(0)
        df['late_payment_count'] = df['late_payment_count'].fillna(0)
        df['late_payment_ratio'] = df['late_payment_ratio'].fillna(0)
        
        self.feature_columns.extend([
            'avg_payment_delay_days',
            'late_payment_count',
            'late_payment_ratio'
        ])
        
        logger.info("Calculated payment history features")
        return df
    
    def calculate_income_stability_score(
        self,
        df: pd.DataFrame,
        employment_length_col: str = 'employment_length'
    ) -> pd.DataFrame:
        """
        Calculate income stability score
        
        Args:
            df: Input DataFrame
            employment_length_col: Column name for employment length
            
        Returns:
            DataFrame with income_stability_score column
        """
        # Score based on employment length (0-10 scale)
        df['income_stability_score'] = (
            df[employment_length_col].fillna(0).clip(upper=10) / 10.0
        )
        
        self.feature_columns.append('income_stability_score')
        logger.info("Calculated income stability score")
        return df
    
    def calculate_default_probability(
        self,
        df: pd.DataFrame,
        model = None
    ) -> pd.DataFrame:
        """
        Calculate default probability using features
        
        Args:
            df: Input DataFrame with features
            model: Trained ML model (if None, use rule-based)
            
        Returns:
            DataFrame with default_probability column
        """
        if model is not None:
            # Use trained model
            feature_cols = [col for col in self.feature_columns if col in df.columns]
            X = df[feature_cols].fillna(0)
            df['default_probability'] = model.predict_proba(X)[:, 1]
        else:
            # Rule-based probability (simplified)
            df['default_probability'] = (
                0.3 * df.get('debt_to_income_ratio', 0) +
                0.2 * df.get('credit_utilization', 0) +
                0.3 * df.get('late_payment_ratio', 0) +
                0.2 * (1 - df.get('income_stability_score', 0.5))
            ).clip(0, 1)
        
        logger.info("Calculated default probability")
        return df
    
    def create_risk_categories(
        self,
        df: pd.DataFrame,
        prob_col: str = 'default_probability'
    ) -> pd.DataFrame:
        """
        Create risk categories based on default probability
        
        Args:
            df: Input DataFrame
            prob_col: Column name for probability
            
        Returns:
            DataFrame with risk_category column
        """
        def categorize_risk(prob):
            if prob < 0.2:
                return 'Low'
            elif prob < 0.5:
                return 'Medium'
            elif prob < 0.75:
                return 'High'
            else:
                return 'Very High'
        
        df['risk_category'] = df[prob_col].apply(categorize_risk)
        
        logger.info("Created risk categories")
        return df
    
    def create_all_features(
        self,
        df: pd.DataFrame,
        payment_history: pd.DataFrame = None,
        model = None
    ) -> pd.DataFrame:
        """
        Create all risk features
        
        Args:
            df: Input DataFrame
            payment_history: Payment history DataFrame
            model: Trained ML model
            
        Returns:
            DataFrame with all features
        """
        df = self.calculate_debt_to_income_ratio(df)
        df = self.calculate_loan_to_value_ratio(df)
        df = self.calculate_credit_utilization(df)
        df = self.calculate_payment_history_features(df, payment_history)
        df = self.calculate_income_stability_score(df)
        df = self.calculate_default_probability(df, model)
        df = self.create_risk_categories(df)
        
        logger.info(f"Created {len(self.feature_columns)} risk features")
        return df
    
    def get_feature_columns(self) -> List[str]:
        """Get list of feature columns"""
        return self.feature_columns
