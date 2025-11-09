"""
Storage connectors for Snowflake, BigQuery, and S3
"""
import os
import boto3
import pandas as pd
from typing import Dict, Any, List
import snowflake.connector
from google.cloud import bigquery
from google.oauth2 import service_account

from ..utils.config_loader import config
from ..utils.logger import setup_logger


logger = setup_logger(__name__)


class SnowflakeConnector:
    """Connector for Snowflake data warehouse"""
    
    def __init__(self):
        """Initialize Snowflake connection"""
        sf_config = config.storage_config.get('snowflake', {})
        
        self.conn_params = {
            'account': sf_config.get('account'),
            'user': sf_config.get('user'),
            'password': sf_config.get('password'),
            'warehouse': sf_config.get('warehouse'),
            'database': sf_config.get('database'),
            'schema': sf_config.get('schema')
        }
        
        self.connection = None
        logger.info("Snowflake connector initialized")
    
    def connect(self):
        """Establish connection to Snowflake"""
        try:
            self.connection = snowflake.connector.connect(**self.conn_params)
            logger.info("Connected to Snowflake")
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {str(e)}")
            raise
    
    def write_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = 'append'
    ):
        """
        Write DataFrame to Snowflake table
        
        Args:
            df: DataFrame to write
            table_name: Target table name
            if_exists: How to behave if table exists ('append', 'replace', 'fail')
        """
        if self.connection is None:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            # Create table if not exists
            if if_exists == 'replace':
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            
            # Write data using pandas
            from snowflake.connector.pandas_tools import write_pandas
            
            success, nchunks, nrows, _ = write_pandas(
                self.connection,
                df,
                table_name,
                auto_create_table=True
            )
            
            logger.info(f"Written {nrows} rows to Snowflake table {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to write to Snowflake: {str(e)}")
            raise
    
    def read_query(self, query: str) -> pd.DataFrame:
        """
        Execute query and return results as DataFrame
        
        Args:
            query: SQL query to execute
            
        Returns:
            Query results as DataFrame
        """
        if self.connection is None:
            self.connect()
        
        try:
            df = pd.read_sql(query, self.connection)
            logger.info(f"Executed query, returned {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Failed to execute query: {str(e)}")
            raise
    
    def close(self):
        """Close Snowflake connection"""
        if self.connection:
            self.connection.close()
            logger.info("Snowflake connection closed")


class BigQueryConnector:
    """Connector for Google BigQuery"""
    
    def __init__(self):
        """Initialize BigQuery client"""
        bq_config = config.storage_config.get('bigquery', {})
        
        self.project_id = bq_config.get('project_id')
        self.dataset = bq_config.get('dataset')
        credentials_path = bq_config.get('credentials_path')
        
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            self.client = bigquery.Client(
                credentials=credentials,
                project=self.project_id
            )
        else:
            self.client = bigquery.Client(project=self.project_id)
        
        logger.info("BigQuery connector initialized")
    
    def write_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = 'append'
    ):
        """
        Write DataFrame to BigQuery table
        
        Args:
            df: DataFrame to write
            table_name: Target table name
            if_exists: How to behave if table exists
        """
        try:
            table_id = f"{self.project_id}.{self.dataset}.{table_name}"
            
            job_config = bigquery.LoadJobConfig(
                write_disposition=(
                    bigquery.WriteDisposition.WRITE_APPEND
                    if if_exists == 'append'
                    else bigquery.WriteDisposition.WRITE_TRUNCATE
                )
            )
            
            job = self.client.load_table_from_dataframe(
                df,
                table_id,
                job_config=job_config
            )
            
            job.result()  # Wait for completion
            
            logger.info(f"Written {len(df)} rows to BigQuery table {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to write to BigQuery: {str(e)}")
            raise
    
    def read_query(self, query: str) -> pd.DataFrame:
        """
        Execute query and return results as DataFrame
        
        Args:
            query: SQL query to execute
            
        Returns:
            Query results as DataFrame
        """
        try:
            df = self.client.query(query).to_dataframe()
            logger.info(f"Executed query, returned {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Failed to execute query: {str(e)}")
            raise
    
    def create_dataset(self, dataset_id: str = None):
        """
        Create BigQuery dataset
        
        Args:
            dataset_id: Dataset ID (uses config default if not provided)
        """
        if dataset_id is None:
            dataset_id = self.dataset
        
        try:
            dataset = bigquery.Dataset(f"{self.project_id}.{dataset_id}")
            dataset.location = "US"
            
            dataset = self.client.create_dataset(dataset, exists_ok=True)
            logger.info(f"Created dataset {dataset_id}")
            
        except Exception as e:
            logger.error(f"Failed to create dataset: {str(e)}")
            raise


class S3Connector:
    """Connector for AWS S3"""
    
    def __init__(self):
        """Initialize S3 client"""
        s3_config = config.storage_config.get('s3', {})
        
        self.bucket = s3_config.get('bucket')
        self.region = s3_config.get('region', 'us-east-1')
        self.raw_prefix = s3_config.get('raw_prefix', 'raw/')
        self.processed_prefix = s3_config.get('processed_prefix', 'processed/')
        
        self.s3_client = boto3.client('s3', region_name=self.region)
        
        logger.info(f"S3 connector initialized for bucket: {self.bucket}")
    
    def upload_dataframe(
        self,
        df: pd.DataFrame,
        key: str,
        file_format: str = 'parquet'
    ):
        """
        Upload DataFrame to S3
        
        Args:
            df: DataFrame to upload
            key: S3 key (path)
            file_format: File format ('parquet', 'csv', 'json')
        """
        try:
            import io
            
            buffer = io.BytesIO()
            
            if file_format == 'parquet':
                df.to_parquet(buffer, index=False)
                content_type = 'application/octet-stream'
            elif file_format == 'csv':
                df.to_csv(buffer, index=False)
                content_type = 'text/csv'
            elif file_format == 'json':
                df.to_json(buffer, orient='records', lines=True)
                content_type = 'application/json'
            else:
                raise ValueError(f"Unsupported format: {file_format}")
            
            buffer.seek(0)
            
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=buffer,
                ContentType=content_type
            )
            
            logger.info(f"Uploaded DataFrame to s3://{self.bucket}/{key}")
            
        except Exception as e:
            logger.error(f"Failed to upload to S3: {str(e)}")
            raise
    
    def download_dataframe(
        self,
        key: str,
        file_format: str = 'parquet'
    ) -> pd.DataFrame:
        """
        Download DataFrame from S3
        
        Args:
            key: S3 key (path)
            file_format: File format
            
        Returns:
            Downloaded DataFrame
        """
        try:
            import io
            
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=key
            )
            
            buffer = io.BytesIO(response['Body'].read())
            
            if file_format == 'parquet':
                df = pd.read_parquet(buffer)
            elif file_format == 'csv':
                df = pd.read_csv(buffer)
            elif file_format == 'json':
                df = pd.read_json(buffer, orient='records', lines=True)
            else:
                raise ValueError(f"Unsupported format: {file_format}")
            
            logger.info(f"Downloaded DataFrame from s3://{self.bucket}/{key}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to download from S3: {str(e)}")
            raise
    
    def list_objects(self, prefix: str = '') -> List[str]:
        """
        List objects in S3 bucket
        
        Args:
            prefix: Prefix to filter objects
            
        Returns:
            List of object keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            
            keys = [obj['Key'] for obj in response.get('Contents', [])]
            logger.info(f"Listed {len(keys)} objects with prefix {prefix}")
            return keys
            
        except Exception as e:
            logger.error(f"Failed to list S3 objects: {str(e)}")
            raise
