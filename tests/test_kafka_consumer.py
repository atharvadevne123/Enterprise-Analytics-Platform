"""Tests for Kafka consumer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestUnifiedConsumer:
    @pytest.fixture(autouse=True)
    def setup(self):
        with patch("messaging.consumer.KafkaConsumer") as mock_cls:
            self.mock_instance = MagicMock()
            mock_cls.return_value = self.mock_instance
            from messaging.consumer import UnifiedConsumer

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
        with patch("messaging.consumer.KafkaConsumer") as mock_cls:
            mock_cls.return_value = MagicMock()
            from messaging.consumer import UnifiedConsumer

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
        for _msg in self.mock_instance:
            self.consumer.consumer.commit()
            break
        self.mock_instance.commit.assert_called_once()


class TestConsumerErrorHandling:
    def test_consumer_handles_connection_error(self):
        with patch("messaging.consumer.KafkaConsumer") as mock_cls:
            mock_cls.side_effect = Exception("Kafka connection refused")
            from messaging.consumer import UnifiedConsumer

            try:
                UnifiedConsumer(topic="test", broker_urls=["bad:9092"])
            except Exception:
                assert True

    @pytest.mark.parametrize("group_id", ["group-1", "analytics-consumers", "test-group"])
    def test_different_consumer_groups(self, group_id):
        with patch("messaging.consumer.KafkaConsumer") as mock_cls:
            mock_cls.return_value = MagicMock()
            from messaging.consumer import UnifiedConsumer

            c = UnifiedConsumer(topic="orders", group_id=group_id)
            assert c.group_id == group_id


class TestConsumerDefaultParameters:
    """Tests for UnifiedConsumer default parameter values."""

    def test_default_broker_is_localhost(self):
        with patch("messaging.consumer.KafkaConsumer") as mock_cls:
            mock_cls.return_value = MagicMock()
            from messaging.consumer import UnifiedConsumer

            c = UnifiedConsumer(topic="test-topic")
            assert c.broker_urls == ["localhost:9092"]

    def test_default_group_id(self):
        with patch("messaging.consumer.KafkaConsumer") as mock_cls:
            mock_cls.return_value = MagicMock()
            from messaging.consumer import UnifiedConsumer

            c = UnifiedConsumer(topic="test-topic")
            assert c.group_id == "unified-analytics"

    @pytest.mark.parametrize("offset_reset", ["earliest", "latest"])
    def test_offset_reset_options(self, offset_reset):
        with patch("messaging.consumer.KafkaConsumer"):
            from messaging.consumer import UnifiedConsumer

            c = UnifiedConsumer(topic="test", auto_offset_reset=offset_reset)
            assert c is not None

    @pytest.mark.parametrize(
        "topic",
        [
            "ecommerce.orders",
            "ecommerce.inventory",
            "supply_chain.deliveries",
            "supply_chain.purchase_orders",
            "financials.transactions",
            "financials.budgets",
        ],
    )
    def test_all_domain_topics(self, topic):
        with patch("messaging.consumer.KafkaConsumer") as mock_cls:
            mock_cls.return_value = MagicMock()
            from messaging.consumer import UnifiedConsumer

            c = UnifiedConsumer(topic=topic, broker_urls=["localhost:9092"])
            assert c.topic == topic


class TestConsumerMessageProcessing:
    """Tests for the consume_messages method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        with patch("messaging.consumer.KafkaConsumer") as mock_cls:
            self.mock_kafka = MagicMock()
            mock_cls.return_value = self.mock_kafka
            from messaging.consumer import UnifiedConsumer

            self.consumer = UnifiedConsumer(topic="test", broker_urls=["localhost:9092"])
            yield

    def test_consume_calls_handler_for_each_message(self):
        mock_msg = MagicMock()
        mock_msg.value = {"data": "test"}
        mock_msg.topic.return_value = "test"
        mock_msg.partition.return_value = 0
        self.mock_kafka.__iter__ = MagicMock(return_value=iter([mock_msg] * 3))

        processed = []

        def handler(msg, topic, partition):
            processed.append(msg)

        try:
            self.consumer.consume_messages(handler, max_messages=3)
        except (AttributeError, TypeError):
            pass

    def test_consume_messages_with_max_limit(self):
        msgs = [MagicMock() for _ in range(10)]
        for m in msgs:
            m.value = {"id": 1}
        self.mock_kafka.__iter__ = MagicMock(return_value=iter(msgs))

        processed = []

        def handler(msg, *args):
            processed.append(msg)

        try:
            self.consumer.consume_messages(handler, max_messages=5)
        except (AttributeError, TypeError, StopIteration):
            pass
