"""
Kafka consumer for consuming loan and transaction data streams
"""
import json
from typing import Callable, Dict, Any
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from ..utils.config_loader import config
from ..utils.logger import setup_logger


logger = setup_logger(__name__)


class LoanDataConsumer:
    """Kafka consumer for loan and transaction data"""
    
    def __init__(self, topics: list = None):
        """
        Initialize Kafka consumer
        
        Args:
            topics: List of topics to subscribe to
        """
        kafka_config = config.kafka_config
        
        if topics is None:
            topics = list(kafka_config.get('topics', {}).values())
        
        self.consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=kafka_config.get('bootstrap_servers'),
            group_id=kafka_config.get('consumer_group'),
            auto_offset_reset=kafka_config.get('auto_offset_reset', 'earliest'),
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None
        )
        
        logger.info(f"Kafka consumer initialized for topics: {topics}")
    
    def consume_messages(
        self,
        process_function: Callable[[str, Dict[str, Any]], None],
        max_messages: int = None
    ):
        """
        Consume messages and process them
        
        Args:
            process_function: Function to process each message
            max_messages: Maximum number of messages to consume (None for infinite)
        """
        message_count = 0
        
        try:
            for message in self.consumer:
                try:
                    # Process the message
                    process_function(message.topic, message.value)
                    
                    message_count += 1
                    
                    if message_count % 100 == 0:
                        logger.info(f"Processed {message_count} messages")
                    
                    # Stop if max_messages reached
                    if max_messages and message_count >= max_messages:
                        logger.info(f"Reached max messages limit: {max_messages}")
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        finally:
            self.close()
    
    def consume_batch(self, batch_size: int = 100, timeout_ms: int = 1000):
        """
        Consume messages in batches
        
        Args:
            batch_size: Number of messages per batch
            timeout_ms: Timeout for polling
            
        Returns:
            List of messages
        """
        messages = []
        
        try:
            batch = self.consumer.poll(
                timeout_ms=timeout_ms,
                max_records=batch_size
            )
            
            for topic_partition, records in batch.items():
                for record in records:
                    messages.append({
                        'topic': record.topic,
                        'partition': record.partition,
                        'offset': record.offset,
                        'key': record.key,
                        'value': record.value,
                        'timestamp': record.timestamp
                    })
            
            logger.info(f"Consumed batch of {len(messages)} messages")
            
        except KafkaError as e:
            logger.error(f"Error consuming batch: {str(e)}")
        
        return messages
    
    def seek_to_beginning(self):
        """Seek to the beginning of all partitions"""
        self.consumer.seek_to_beginning()
        logger.info("Seeked to beginning of all partitions")
    
    def seek_to_end(self):
        """Seek to the end of all partitions"""
        self.consumer.seek_to_end()
        logger.info("Seeked to end of all partitions")
    
    def close(self):
        """Close the Kafka consumer"""
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")
