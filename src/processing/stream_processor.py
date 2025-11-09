"""
Spark Structured Streaming processor for loan and transaction data
"""
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, from_json, to_timestamp, window, avg, sum as spark_sum,
    count, lag, datediff, current_timestamp, when, lit
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    TimestampType, IntegerType, BooleanType
)
from pyspark.sql.window import Window

from ..utils.config_loader import config
from ..utils.logger import setup_logger


logger = setup_logger(__name__)


class LoanStreamProcessor:
    """Spark Structured Streaming processor for loan data"""
    
    def __init__(self):
        """Initialize Spark session"""
        spark_config = config.spark_config
        
        self.spark = SparkSession.builder \
            .appName(spark_config.get('app_name', 'LoanDefaultRiskPipeline')) \
            .master(spark_config.get('master', 'local[*]')) \
            .config("spark.sql.shuffle.partitions", "4") \
            .config("spark.streaming.stopGracefullyOnShutdown", "true") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        
        self.checkpoint_location = spark_config.get('checkpoint_location')
        self.output_mode = spark_config.get('output_mode', 'append')
        self.trigger_interval = spark_config.get('trigger_interval', '30 seconds')
        
        logger.info("Spark Structured Streaming initialized")
    
    def get_loan_application_schema(self) -> StructType:
        """Define schema for loan application data"""
        return StructType([
            StructField("application_id", StringType(), False),
            StructField("customer_id", StringType(), False),
            StructField("loan_amount", DoubleType(), False),
            StructField("loan_term_months", IntegerType(), False),
            StructField("interest_rate", DoubleType(), False),
            StructField("annual_income", DoubleType(), False),
            StructField("employment_length", IntegerType(), True),
            StructField("home_ownership", StringType(), True),
            StructField("loan_purpose", StringType(), True),
            StructField("credit_score", IntegerType(), True),
            StructField("debt_amount", DoubleType(), True),
            StructField("application_timestamp", StringType(), False),
            StructField("ingestion_timestamp", StringType(), False)
        ])
    
    def get_transaction_schema(self) -> StructType:
        """Define schema for transaction data"""
        return StructType([
            StructField("transaction_id", StringType(), False),
            StructField("customer_id", StringType(), False),
            StructField("amount", DoubleType(), False),
            StructField("transaction_type", StringType(), False),
            StructField("category", StringType(), True),
            StructField("timestamp", StringType(), False),
            StructField("status", StringType(), True),
            StructField("ingestion_timestamp", StringType(), False)
        ])
    
    def get_repayment_schema(self) -> StructType:
        """Define schema for repayment data"""
        return StructType([
            StructField("repayment_id", StringType(), False),
            StructField("loan_id", StringType(), False),
            StructField("customer_id", StringType(), False),
            StructField("amount_paid", DoubleType(), False),
            StructField("amount_due", DoubleType(), False),
            StructField("payment_date", StringType(), False),
            StructField("due_date", StringType(), False),
            StructField("status", StringType(), False),
            StructField("days_late", IntegerType(), True),
            StructField("ingestion_timestamp", StringType(), False)
        ])
    
    def read_kafka_stream(self, topic: str, schema: StructType) -> DataFrame:
        """
        Read streaming data from Kafka
        
        Args:
            topic: Kafka topic name
            schema: Schema for the data
            
        Returns:
            Streaming DataFrame
        """
        kafka_config = config.kafka_config
        
        df = self.spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", kafka_config.get('bootstrap_servers')) \
            .option("subscribe", topic) \
            .option("startingOffsets", "earliest") \
            .load()
        
        # Parse JSON value
        parsed_df = df.select(
            from_json(col("value").cast("string"), schema).alias("data")
        ).select("data.*")
        
        # Convert timestamp strings to timestamp type
        if "timestamp" in parsed_df.columns:
            parsed_df = parsed_df.withColumn(
                "timestamp",
                to_timestamp(col("timestamp"))
            )
        
        if "application_timestamp" in parsed_df.columns:
            parsed_df = parsed_df.withColumn(
                "application_timestamp",
                to_timestamp(col("application_timestamp"))
            )
        
        logger.info(f"Reading stream from Kafka topic: {topic}")
        return parsed_df
    
    def compute_risk_features(self, loan_df: DataFrame, transaction_df: DataFrame) -> DataFrame:
        """
        Compute risk features from loan and transaction data
        
        Args:
            loan_df: Loan application DataFrame
            transaction_df: Transaction DataFrame
            
        Returns:
            DataFrame with risk features
        """
        # Calculate debt-to-income ratio
        loan_with_features = loan_df.withColumn(
            "debt_to_income_ratio",
            (col("debt_amount") + col("loan_amount")) / col("annual_income")
        )
        
        # Calculate loan-to-value ratio (simplified)
        loan_with_features = loan_with_features.withColumn(
            "loan_to_value_ratio",
            col("loan_amount") / (col("annual_income") * col("loan_term_months") / 12)
        )
        
        # Aggregate transaction data per customer
        transaction_agg = transaction_df.groupBy("customer_id").agg(
            avg("amount").alias("avg_transaction_amount"),
            spark_sum("amount").alias("total_transaction_amount"),
            count("*").alias("transaction_count")
        )
        
        # Join loan data with transaction aggregates
        enriched_df = loan_with_features.join(
            transaction_agg,
            "customer_id",
            "left"
        )
        
        # Calculate credit utilization (simplified)
        enriched_df = enriched_df.withColumn(
            "credit_utilization",
            when(
                col("total_transaction_amount").isNotNull(),
                col("debt_amount") / col("total_transaction_amount")
            ).otherwise(0.5)
        )
        
        logger.info("Computed risk features")
        return enriched_df
    
    def compute_payment_delays(self, repayment_df: DataFrame) -> DataFrame:
        """
        Compute payment delay metrics
        
        Args:
            repayment_df: Repayment DataFrame
            
        Returns:
            DataFrame with payment delay features
        """
        # Convert date strings to timestamp
        repayment_df = repayment_df \
            .withColumn("payment_date", to_timestamp(col("payment_date"))) \
            .withColumn("due_date", to_timestamp(col("due_date")))
        
        # Calculate payment delay in days
        repayment_df = repayment_df.withColumn(
            "payment_delay_days",
            when(
                col("days_late").isNotNull(),
                col("days_late")
            ).otherwise(
                datediff(col("payment_date"), col("due_date"))
            )
        )
        
        # Aggregate by customer
        delay_metrics = repayment_df.groupBy("customer_id").agg(
            avg("payment_delay_days").alias("avg_payment_delay_days"),
            spark_sum(
                when(col("payment_delay_days") > 0, 1).otherwise(0)
            ).alias("late_payment_count"),
            count("*").alias("total_payments")
        )
        
        # Calculate late payment ratio
        delay_metrics = delay_metrics.withColumn(
            "late_payment_ratio",
            col("late_payment_count") / col("total_payments")
        )
        
        logger.info("Computed payment delay metrics")
        return delay_metrics
    
    def write_to_console(self, df: DataFrame, query_name: str):
        """
        Write streaming data to console (for debugging)
        
        Args:
            df: DataFrame to write
            query_name: Name for the streaming query
        """
        query = df.writeStream \
            .outputMode(self.output_mode) \
            .format("console") \
            .queryName(query_name) \
            .trigger(processingTime=self.trigger_interval) \
            .start()
        
        logger.info(f"Started streaming query: {query_name}")
        return query
    
    def write_to_parquet(
        self,
        df: DataFrame,
        output_path: str,
        query_name: str,
        partition_by: list = None
    ):
        """
        Write streaming data to Parquet files
        
        Args:
            df: DataFrame to write
            output_path: Output directory path
            query_name: Name for the streaming query
            partition_by: Columns to partition by
        """
        writer = df.writeStream \
            .outputMode(self.output_mode) \
            .format("parquet") \
            .queryName(query_name) \
            .option("path", output_path) \
            .option("checkpointLocation", f"{self.checkpoint_location}/{query_name}") \
            .trigger(processingTime=self.trigger_interval)
        
        if partition_by:
            writer = writer.partitionBy(*partition_by)
        
        query = writer.start()
        
        logger.info(f"Started streaming query to Parquet: {query_name}")
        return query
    
    def stop(self):
        """Stop the Spark session"""
        if self.spark:
            self.spark.stop()
            logger.info("Spark session stopped")
