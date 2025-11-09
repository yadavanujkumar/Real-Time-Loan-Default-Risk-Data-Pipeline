"""
Airflow DAG for orchestrating the loan default risk pipeline
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.ingestion.api_client import FintechAPIClient
from src.ingestion.kafka_producer import LoanDataProducer
from src.processing.feature_engineering import RiskFeatureEngineer
from src.models.loan_default_model import LoanDefaultModel
from src.storage.connectors import SnowflakeConnector, BigQueryConnector, S3Connector
from src.utils.config_loader import config
from src.utils.logger import setup_logger


logger = setup_logger(__name__)


# Default arguments for the DAG
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}


def ingest_api_data(**context):
    """Task to ingest data from fintech APIs"""
    logger.info("Starting API data ingestion")
    
    api_client = FintechAPIClient()
    producer = LoanDataProducer()
    
    # Fetch transactions
    transactions = api_client.get_razorpay_transactions(limit=100)
    
    # Send to Kafka
    success_count = producer.send_batch(
        config.kafka_config['topics']['transactions'],
        transactions
    )
    
    producer.close()
    
    logger.info(f"Ingested {success_count} transactions from API")
    return success_count


def process_features(**context):
    """Task to process features"""
    logger.info("Starting feature processing")
    
    import pandas as pd
    
    # Load data (from S3 or other storage)
    s3_connector = S3Connector()
    
    try:
        # Try to load recent data
        df = s3_connector.download_dataframe(
            f"{s3_connector.raw_prefix}loan_applications.parquet"
        )
    except:
        # Generate sample data for demo
        df = pd.DataFrame({
            'customer_id': [f'cust_{i}' for i in range(100)],
            'loan_amount': [10000 + i * 1000 for i in range(100)],
            'annual_income': [50000 + i * 500 for i in range(100)],
            'debt_amount': [5000 + i * 100 for i in range(100)],
            'employment_length': [i % 10 for i in range(100)],
            'credit_score': [650 + i for i in range(100)]
        })
    
    # Engineer features
    feature_engineer = RiskFeatureEngineer()
    df = feature_engineer.create_all_features(df)
    
    # Save processed data
    s3_connector.upload_dataframe(
        df,
        f"{s3_connector.processed_prefix}loan_features_{datetime.now().strftime('%Y%m%d')}.parquet"
    )
    
    logger.info(f"Processed features for {len(df)} records")
    return len(df)


def train_model(**context):
    """Task to train ML model"""
    logger.info("Starting model training")
    
    import pandas as pd
    import numpy as np
    
    # Load processed data
    s3_connector = S3Connector()
    
    try:
        df = s3_connector.download_dataframe(
            f"{s3_connector.processed_prefix}loan_features_{datetime.now().strftime('%Y%m%d')}.parquet"
        )
    except:
        logger.warning("No processed data found, using sample data")
        # Generate sample data with target
        df = pd.DataFrame({
            'debt_to_income_ratio': np.random.uniform(0.1, 0.9, 100),
            'loan_to_value_ratio': np.random.uniform(0.2, 1.5, 100),
            'credit_utilization': np.random.uniform(0.1, 1.0, 100),
            'income_stability_score': np.random.uniform(0.3, 1.0, 100),
            'default': np.random.choice([0, 1], 100, p=[0.8, 0.2])
        })
    
    # Ensure we have a target column
    if 'default' not in df.columns:
        # Generate synthetic target based on risk features
        df['default'] = (
            (df['debt_to_income_ratio'] > 0.5).astype(int) |
            (df.get('credit_utilization', 0.5) > 0.7).astype(int)
        )
    
    # Train model
    model = LoanDefaultModel(model_type='random_forest')
    X, y = model.prepare_features(df, target_col='default')
    metrics = model.train(X, y)
    
    # Save model
    model_path = f"/tmp/loan_default_model_{datetime.now().strftime('%Y%m%d')}.pkl"
    model.save_model(model_path)
    
    # Upload to S3
    import shutil
    with open(model_path, 'rb') as f:
        s3_connector.s3_client.put_object(
            Bucket=s3_connector.bucket,
            Key=f"models/loan_default_model_{datetime.now().strftime('%Y%m%d')}.pkl",
            Body=f
        )
    
    logger.info(f"Model trained with metrics: {metrics}")
    return metrics


def load_to_warehouse(**context):
    """Task to load data to data warehouse"""
    logger.info("Starting data warehouse load")
    
    import pandas as pd
    
    # Load processed data
    s3_connector = S3Connector()
    
    try:
        df = s3_connector.download_dataframe(
            f"{s3_connector.processed_prefix}loan_features_{datetime.now().strftime('%Y%m%d')}.parquet"
        )
    except:
        logger.warning("No processed data found")
        return 0
    
    # Try Snowflake first
    try:
        sf_connector = SnowflakeConnector()
        sf_connector.write_dataframe(df, 'loan_risk_features')
        sf_connector.close()
        logger.info(f"Loaded {len(df)} rows to Snowflake")
    except Exception as e:
        logger.warning(f"Snowflake load failed: {str(e)}")
        
        # Fallback to BigQuery
        try:
            bq_connector = BigQueryConnector()
            bq_connector.write_dataframe(df, 'loan_risk_features')
            logger.info(f"Loaded {len(df)} rows to BigQuery")
        except Exception as e:
            logger.error(f"BigQuery load also failed: {str(e)}")
            raise
    
    return len(df)


def generate_risk_report(**context):
    """Task to generate risk analysis report"""
    logger.info("Generating risk report")
    
    import pandas as pd
    
    s3_connector = S3Connector()
    
    try:
        df = s3_connector.download_dataframe(
            f"{s3_connector.processed_prefix}loan_features_{datetime.now().strftime('%Y%m%d')}.parquet"
        )
        
        # Generate summary statistics
        report = {
            'total_applications': len(df),
            'avg_default_probability': df.get('default_probability', pd.Series([0])).mean(),
            'high_risk_count': len(df[df.get('risk_category', '') == 'High']),
            'low_risk_count': len(df[df.get('risk_category', '') == 'Low']),
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info(f"Risk report: {report}")
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate report: {str(e)}")
        return {}


# Define the DAG
with DAG(
    'loan_default_risk_pipeline',
    default_args=default_args,
    description='End-to-end loan default risk prediction pipeline',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    catchup=False,
    tags=['loan', 'risk', 'ml'],
) as dag:
    
    # Task 1: Ingest data from APIs
    ingest_task = PythonOperator(
        task_id='ingest_api_data',
        python_callable=ingest_api_data,
        provide_context=True,
    )
    
    # Task 2: Process features
    process_task = PythonOperator(
        task_id='process_features',
        python_callable=process_features,
        provide_context=True,
    )
    
    # Task 3: Train model
    train_task = PythonOperator(
        task_id='train_model',
        python_callable=train_model,
        provide_context=True,
    )
    
    # Task 4: Load to warehouse
    load_task = PythonOperator(
        task_id='load_to_warehouse',
        python_callable=load_to_warehouse,
        provide_context=True,
    )
    
    # Task 5: Generate report
    report_task = PythonOperator(
        task_id='generate_risk_report',
        python_callable=generate_risk_report,
        provide_context=True,
    )
    
    # Define task dependencies
    ingest_task >> process_task >> [train_task, load_task] >> report_task
