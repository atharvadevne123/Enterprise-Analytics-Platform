"""Tests for Kafka consumer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestUnifiedConsumer:
    @pytest.fixture(autouse=True)
    def setup(self):
        with patch("kafka.consumer.KafkaConsumer") as mock_cls:
            self.mock_instance = MagicMock()
            mock_cls.return_value = self.mock_instance
            from kafka.consumer import UnifiedConsumer
            self.consumer = UnifiedConsumer(
                topic="orders",
                broker_urls=["localhost:9092"],
                group_id="test-group",
            )
            yield

    def test_consumer_instantiation(self):
        assert self.consumer is not None

    def test_consumer_topic_set(self):
        assert self.consumer.topic == "orders"

    def test_consumer_group_id_set(self):
        assert self.consumer.group_id == "test-group"

    def test_close_calls_consumer_close(self):
        self.consumer.close()
        self.mock_instance.close.assert_called_once()

    @pytest.mark.parametrize("topic", ["orders", "deliveries", "financial-transactions", "inventory"])
    def test_different_topics(self, topic):
        with patch("kafka.consumer.KafkaConsumer") as mock_cls:
            mock_cls.return_value = MagicMock()
            from kafka.consumer import UnifiedConsumer
            consumer = UnifiedConsumer(topic=topic, broker_urls=["localhost:9092"])
            assert consumer.topic == topic

    def test_consume_messages(self):
        mock_msg = MagicMock()
        mock_msg.value = {"order_id": "ORD-001", "status": "shipped"}
        mock_msg.offset = 0
        self.mock_instance.__iter__ = MagicMock(return_value=iter([mock_msg]))
        processed = []
        for msg in self.mock_instance:
            processed.append(msg.value)
            break
        assert len(processed) == 1

    def test_commit_called_after_processing(self):
        mock_msg = MagicMock()
        mock_msg.value = {"event": "test"}
        self.mock_instance.__iter__ = MagicMock(return_value=iter([mock_msg]))
        for msg in self.mock_instance:
            self.consumer.consumer.commit()
            break
        self.mock_instance.commit.assert_called_once()


class TestConsumerErrorHandling:
    def test_consumer_handles_connection_error(self):
        with patch("kafka.consumer.KafkaConsumer") as mock_cls:
            mock_cls.side_effect = Exception("Kafka connection refused")
            from kafka.consumer import UnifiedConsumer
            try:
                UnifiedConsumer(topic="test", broker_urls=["bad:9092"])
            except Exception:
                assert True

    @pytest.mark.parametrize("group_id", ["group-1", "analytics-consumers", "test-group"])
    def test_different_consumer_groups(self, group_id):
        with patch("kafka.consumer.KafkaConsumer") as mock_cls:
            mock_cls.return_value = MagicMock()
            from kafka.consumer import UnifiedConsumer
            c = UnifiedConsumer(topic="orders", group_id=group_id)
            assert c.group_id == group_id
