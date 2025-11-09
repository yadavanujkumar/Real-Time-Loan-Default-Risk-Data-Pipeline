"""
Kafka producer for ingesting loan application and transaction data
"""
import json
import time
from typing import Dict, Any, List
from kafka import KafkaProducer
from kafka.errors import KafkaError
from datetime import datetime

from ..utils.config_loader import config
from ..utils.logger import setup_logger


logger = setup_logger(__name__)


class LoanDataProducer:
    """Kafka producer for loan and transaction data"""
    
    def __init__(self):
        """Initialize Kafka producer"""
        kafka_config = config.kafka_config
        
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_config.get('bootstrap_servers'),
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
            max_in_flight_requests_per_connection=1
        )
        
        self.topics = kafka_config.get('topics', {})
        logger.info(f"Kafka producer initialized with topics: {list(self.topics.keys())}")
    
    def send_loan_application(self, application_data: Dict[str, Any]) -> bool:
        """
        Send loan application data to Kafka
        
        Args:
            application_data: Loan application details
            
        Returns:
            Success status
        """
        try:
            # Add metadata
            application_data['ingestion_timestamp'] = datetime.utcnow().isoformat()
            
            # Send to Kafka
            future = self.producer.send(
                self.topics.get('loan_applications'),
                key=application_data.get('application_id'),
                value=application_data
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Loan application sent to Kafka: "
                f"topic={record_metadata.topic}, "
                f"partition={record_metadata.partition}, "
                f"offset={record_metadata.offset}"
            )
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send loan application to Kafka: {str(e)}")
            return False
    
    def send_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """
        Send transaction data to Kafka
        
        Args:
            transaction_data: Transaction details
            
        Returns:
            Success status
        """
        try:
            transaction_data['ingestion_timestamp'] = datetime.utcnow().isoformat()
            
            future = self.producer.send(
                self.topics.get('transactions'),
                key=transaction_data.get('transaction_id'),
                value=transaction_data
            )
            
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Transaction sent to Kafka: "
                f"topic={record_metadata.topic}, "
                f"partition={record_metadata.partition}"
            )
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send transaction to Kafka: {str(e)}")
            return False
    
    def send_repayment(self, repayment_data: Dict[str, Any]) -> bool:
        """
        Send repayment data to Kafka
        
        Args:
            repayment_data: Repayment details
            
        Returns:
            Success status
        """
        try:
            repayment_data['ingestion_timestamp'] = datetime.utcnow().isoformat()
            
            future = self.producer.send(
                self.topics.get('repayments'),
                key=repayment_data.get('loan_id'),
                value=repayment_data
            )
            
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Repayment sent to Kafka: "
                f"topic={record_metadata.topic}, "
                f"partition={record_metadata.partition}"
            )
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send repayment to Kafka: {str(e)}")
            return False
    
    def send_batch(self, topic: str, data_batch: List[Dict[str, Any]]) -> int:
        """
        Send a batch of records to Kafka
        
        Args:
            topic: Target topic
            data_batch: List of records
            
        Returns:
            Number of successfully sent records
        """
        success_count = 0
        
        for record in data_batch:
            try:
                record['ingestion_timestamp'] = datetime.utcnow().isoformat()
                
                self.producer.send(
                    topic,
                    key=record.get('id'),
                    value=record
                )
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send record to {topic}: {str(e)}")
        
        # Flush to ensure all messages are sent
        self.producer.flush()
        
        logger.info(f"Sent {success_count}/{len(data_batch)} records to {topic}")
        return success_count
    
    def close(self):
        """Close the Kafka producer"""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")
