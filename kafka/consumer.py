"""
Kafka Consumers for all domains
Handles real-time event consumption from Kafka topics
"""

import json
import logging
from typing import Callable, Optional
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from datetime import datetime

logger = logging.getLogger(__name__)


class UnifiedConsumer:
    """Unified Kafka consumer for all domains"""

    def __init__(self,
                 topic: str,
                 broker_urls: list = None,
                 group_id: str = "unified-analytics",
                 auto_offset_reset: str = "earliest"):
        """
        Initialize Kafka consumer

        Args:
            topic: Kafka topic to consume
            broker_urls: List of Kafka broker addresses
            group_id: Consumer group ID
            auto_offset_reset: Start position for new consumer groups
        """
        if broker_urls is None:
            broker_urls = ["localhost:9092"]

        self.topic = topic
        self.broker_urls = broker_urls
        self.group_id = group_id

        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=broker_urls,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000,
            max_poll_records=500,
            max_poll_interval_ms=300000
        )

        logger.info(f"Kafka consumer initialized for topic: {topic}")

    def consume_messages(self,
                        message_handler: Callable,
                        timeout_ms: int = 1000,
                        max_messages: Optional[int] = None):
        """
        Consume messages from Kafka

        Args:
            message_handler: Callback function to process each message
            timeout_ms: Timeout for message polling
            max_messages: Maximum messages to process (None = infinite)
        """
        message_count = 0

        try:
            while True:
                messages = self.consumer.poll(timeout_ms=timeout_ms)

                if not messages:
                    logger.debug(f"No messages received from {self.topic}")
                    continue

                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            # Process the message
                            message_handler(record.value, record.topic, record.partition)
                            message_count += 1

                            # Check max messages limit
                            if max_messages and message_count >= max_messages:
                                logger.info(f"Reached max messages limit: {max_messages}")
                                return message_count

                        except Exception as e:
                            logger.error(f"Error processing message: {e}", exc_info=True)

                    # Commit offsets after processing batch
                    try:
                        self.consumer.commit()
                    except Exception as e:
                        logger.error(f"Error committing offsets: {e}")

        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
        finally:
            self.consumer.close()

        return message_count

    def consume_batch(self,
                     message_handler: Callable,
                     batch_size: int = 100,
                     timeout_ms: int = 5000) -> int:
        """
        Consume messages in batches

        Args:
            message_handler: Callback function to process batch
            batch_size: Number of messages per batch
            timeout_ms: Timeout for message polling

        Returns:
            Total number of messages processed
        """
        batch = []
        message_count = 0

        try:
            while True:
                messages = self.consumer.poll(timeout_ms=timeout_ms, max_records=batch_size)

                if not messages:
                    if batch:
                        # Process remaining batch
                        message_handler(batch)
                        message_count += len(batch)
                        batch = []
                    continue

                for topic_partition, records in messages.items():
                    for record in records:
                        batch.append(record.value)

                        if len(batch) >= batch_size:
                            try:
                                message_handler(batch)
                                message_count += len(batch)
                                batch = []
                                self.consumer.commit()
                            except Exception as e:
                                logger.error(f"Error processing batch: {e}", exc_info=True)

        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
        finally:
            if batch:
                try:
                    message_handler(batch)
                    message_count += len(batch)
                except Exception as e:
                    logger.error(f"Error processing final batch: {e}")

            self.consumer.close()

        return message_count

    def close(self):
        """Close the consumer"""
        self.consumer.close()
        logger.info("Consumer closed")


class MultiTopicConsumer:
    """Consumer for multiple Kafka topics"""

    def __init__(self,
                 topics: list,
                 broker_urls: list = None,
                 group_id: str = "unified-analytics",
                 auto_offset_reset: str = "earliest"):
        """
        Initialize multi-topic consumer

        Args:
            topics: List of Kafka topics
            broker_urls: List of Kafka broker addresses
            group_id: Consumer group ID
            auto_offset_reset: Start position
        """
        if broker_urls is None:
            broker_urls = ["localhost:9092"]

        self.topics = topics
        self.broker_urls = broker_urls
        self.group_id = group_id

        self.consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=broker_urls,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000,
            max_poll_records=500
        )

        logger.info(f"Multi-topic consumer initialized for topics: {topics}")

    def consume_messages(self,
                        message_handler: Callable,
                        timeout_ms: int = 1000):
        """
        Consume messages from all subscribed topics

        Args:
            message_handler: Callback function(message, topic, partition)
            timeout_ms: Timeout for message polling
        """
        message_count = 0

        try:
            while True:
                messages = self.consumer.poll(timeout_ms=timeout_ms)

                if not messages:
                    logger.debug("No messages received")
                    continue

                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            message_handler(
                                record.value,
                                record.topic,
                                record.partition
                            )
                            message_count += 1
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")

                    try:
                        self.consumer.commit()
                    except Exception as e:
                        logger.error(f"Error committing offsets: {e}")

        except KeyboardInterrupt:
            logger.info("Consumer interrupted")
        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
        finally:
            self.consumer.close()

        return message_count

    def close(self):
        """Close the consumer"""
        self.consumer.close()
        logger.info("Multi-topic consumer closed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    def process_message(message, topic, partition):
        print(f"[{topic}:{partition}] {message}")

    # Example: consume from single topic
    consumer = UnifiedConsumer('ecommerce.orders')
    try:
        consumer.consume_messages(process_message, max_messages=10)
    finally:
        consumer.close()
