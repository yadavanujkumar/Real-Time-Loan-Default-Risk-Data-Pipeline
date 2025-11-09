"""
Main pipeline orchestrator for real-time loan default risk prediction
"""
import argparse
import sys
import time
from datetime import datetime

from src.ingestion.kafka_producer import LoanDataProducer
from src.ingestion.kafka_consumer import LoanDataConsumer
from src.ingestion.api_client import FintechAPIClient
from src.processing.stream_processor import LoanStreamProcessor
from src.processing.feature_engineering import RiskFeatureEngineer
from src.models.loan_default_model import LoanDefaultModel
from src.storage.connectors import S3Connector, SnowflakeConnector, BigQueryConnector
from src.utils.config_loader import config
from src.utils.logger import setup_logger


logger = setup_logger(__name__, log_dir='logs')


class LoanDefaultRiskPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self):
        """Initialize pipeline components"""
        logger.info("Initializing Loan Default Risk Pipeline")
        
        self.api_client = FintechAPIClient()
        self.kafka_producer = LoanDataProducer()
        self.stream_processor = LoanStreamProcessor()
        self.feature_engineer = RiskFeatureEngineer()
        self.s3_connector = S3Connector()
        
        logger.info("Pipeline components initialized")
    
    def run_batch_ingestion(self, limit: int = 100):
        """
        Run batch data ingestion from APIs
        
        Args:
            limit: Number of records to fetch
        """
        logger.info(f"Starting batch ingestion (limit: {limit})")
        
        # Fetch transactions from APIs
        transactions = self.api_client.get_razorpay_transactions(limit=limit)
        
        # Send to Kafka
        topic = config.kafka_config['topics']['transactions']
        success_count = self.kafka_producer.send_batch(topic, transactions)
        
        logger.info(f"Batch ingestion completed: {success_count} records sent to Kafka")
        return success_count
    
    def run_stream_processing(self, duration_seconds: int = None):
        """
        Run real-time stream processing
        
        Args:
            duration_seconds: How long to run (None for indefinite)
        """
        logger.info("Starting stream processing")
        
        # Read streams
        kafka_config = config.kafka_config
        
        loan_stream = self.stream_processor.read_kafka_stream(
            kafka_config['topics']['loan_applications'],
            self.stream_processor.get_loan_application_schema()
        )
        
        transaction_stream = self.stream_processor.read_kafka_stream(
            kafka_config['topics']['transactions'],
            self.stream_processor.get_transaction_schema()
        )
        
        # Process features
        enriched_stream = self.stream_processor.compute_risk_features(
            loan_stream,
            transaction_stream
        )
        
        # Write to output
        output_path = f"{self.s3_connector.processed_prefix}streaming_output"
        query = self.stream_processor.write_to_parquet(
            enriched_stream,
            output_path,
            'loan_risk_stream'
        )
        
        # Wait for specified duration or until interrupted
        if duration_seconds:
            logger.info(f"Stream processing will run for {duration_seconds} seconds")
            time.sleep(duration_seconds)
            query.stop()
        else:
            logger.info("Stream processing running indefinitely (Ctrl+C to stop)")
            query.awaitTermination()
        
        logger.info("Stream processing completed")
    
    def run_batch_processing(self):
        """Run batch feature engineering and model training"""
        logger.info("Starting batch processing")
        
        import pandas as pd
        import numpy as np
        
        # Generate or load sample data
        df = pd.DataFrame({
            'customer_id': [f'cust_{i}' for i in range(500)],
            'loan_amount': np.random.uniform(5000, 50000, 500),
            'loan_term_months': np.random.choice([12, 24, 36, 48, 60], 500),
            'interest_rate': np.random.uniform(5, 20, 500),
            'annual_income': np.random.uniform(30000, 150000, 500),
            'employment_length': np.random.randint(0, 15, 500),
            'debt_amount': np.random.uniform(1000, 30000, 500),
            'credit_score': np.random.randint(550, 850, 500)
        })
        
        # Engineer features
        df = self.feature_engineer.create_all_features(df)
        
        # Save to S3
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.s3_connector.upload_dataframe(
            df,
            f"{self.s3_connector.processed_prefix}loan_features_{timestamp}.parquet"
        )
        
        logger.info(f"Batch processing completed: {len(df)} records processed")
        return df
    
    def train_model(self, df=None):
        """
        Train ML model
        
        Args:
            df: DataFrame with features (if None, will load from S3)
        """
        logger.info("Starting model training")
        
        import pandas as pd
        import numpy as np
        
        if df is None:
            # Try to load latest data
            try:
                timestamp = datetime.now().strftime('%Y%m%d')
                df = self.s3_connector.download_dataframe(
                    f"{self.s3_connector.processed_prefix}loan_features_{timestamp}.parquet"
                )
            except:
                logger.warning("No data found, generating sample data")
                df = pd.DataFrame({
                    'debt_to_income_ratio': np.random.uniform(0.1, 0.9, 500),
                    'loan_to_value_ratio': np.random.uniform(0.2, 1.5, 500),
                    'credit_utilization': np.random.uniform(0.1, 1.0, 500),
                    'income_stability_score': np.random.uniform(0.3, 1.0, 500),
                    'default': np.random.choice([0, 1], 500, p=[0.8, 0.2])
                })
        
        # Add synthetic target if not present
        if 'default' not in df.columns:
            df['default'] = (
                (df['debt_to_income_ratio'] > 0.6) |
                (df.get('credit_utilization', 0.5) > 0.8)
            ).astype(int)
        
        # Train model
        model = LoanDefaultModel(model_type='random_forest')
        X, y = model.prepare_features(df, target_col='default')
        metrics = model.train(X, y)
        
        # Save model
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = f"/tmp/loan_default_model_{timestamp}.pkl"
        model.save_model(model_path)
        
        # Upload to S3
        with open(model_path, 'rb') as f:
            self.s3_connector.s3_client.put_object(
                Bucket=self.s3_connector.bucket,
                Key=f"models/loan_default_model_{timestamp}.pkl",
                Body=f
            )
        
        logger.info(f"Model training completed with metrics: {metrics}")
        return metrics
    
    def load_to_warehouse(self, df=None):
        """
        Load data to data warehouse
        
        Args:
            df: DataFrame to load (if None, will load from S3)
        """
        logger.info("Starting data warehouse load")
        
        if df is None:
            # Load latest processed data
            timestamp = datetime.now().strftime('%Y%m%d')
            df = self.s3_connector.download_dataframe(
                f"{self.s3_connector.processed_prefix}loan_features_{timestamp}.parquet"
            )
        
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
    
    def run_full_pipeline(self):
        """Run the complete end-to-end pipeline"""
        logger.info("Starting full pipeline execution")
        
        # Step 1: Batch ingestion
        self.run_batch_ingestion(limit=100)
        
        # Step 2: Batch processing
        df = self.run_batch_processing()
        
        # Step 3: Train model
        self.train_model(df)
        
        # Step 4: Load to warehouse
        try:
            self.load_to_warehouse(df)
        except Exception as e:
            logger.warning(f"Warehouse load failed: {str(e)}")
        
        logger.info("Full pipeline execution completed")
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources")
        self.kafka_producer.close()
        self.stream_processor.stop()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Loan Default Risk Data Pipeline'
    )
    parser.add_argument(
        '--mode',
        choices=['batch', 'stream', 'full', 'train', 'dashboard'],
        default='full',
        help='Pipeline execution mode'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=None,
        help='Duration in seconds (for stream mode)'
    )
    
    args = parser.parse_args()
    
    pipeline = LoanDefaultRiskPipeline()
    
    try:
        if args.mode == 'batch':
            pipeline.run_batch_ingestion()
            pipeline.run_batch_processing()
        elif args.mode == 'stream':
            pipeline.run_stream_processing(duration_seconds=args.duration)
        elif args.mode == 'train':
            pipeline.train_model()
        elif args.mode == 'dashboard':
            logger.info("Starting dashboard...")
            from dashboards.risk_dashboard import app
            app.run_server(debug=False)
        else:  # full
            pipeline.run_full_pipeline()
    
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}")
        raise
    finally:
        pipeline.cleanup()


if __name__ == '__main__':
    main()
