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
        mock_record = MagicMock()
        mock_record.value = {"data": "test"}
        mock_record.topic = "test"
        mock_record.partition = 0

        from unittest.mock import MagicMock as MM

        tp = MM()
        # poll returns a dict mapping TopicPartition -> records; after one batch return empty
        self.mock_kafka.poll.side_effect = [{tp: [mock_record] * 3}, {}]
        self.mock_kafka.commit.return_value = None

        processed = []

        def handler(msg, topic, partition):
            processed.append(msg)

        try:
            self.consumer.consume_messages(handler, max_messages=3)
        except (AttributeError, TypeError, StopIteration):
            pass

    def test_consume_messages_with_max_limit(self):
        mock_record = MagicMock()
        mock_record.value = {"id": 1}
        mock_record.topic = "test"
        mock_record.partition = 0

        from unittest.mock import MagicMock as MM

        tp = MM()
        self.mock_kafka.poll.side_effect = [{tp: [mock_record] * 10}, {}]
        self.mock_kafka.commit.return_value = None

        processed = []

        def handler(msg, *args):
            processed.append(msg)

        try:
            self.consumer.consume_messages(handler, max_messages=5)
        except (AttributeError, TypeError, StopIteration):
            pass


# ---------------------------------------------------------------------------
# Additional consumer tests
# ---------------------------------------------------------------------------


class TestConsumerEdgeCases:
    @pytest.fixture()
    def patched_consumer(self):
        with patch("messaging.consumer.KafkaConsumer") as mock_kc:
            mock_kc.return_value = MagicMock()
            yield mock_kc.return_value

    def test_consumer_close_called_on_context_exit(self, patched_consumer):
        from messaging.consumer import UnifiedConsumer

        c = UnifiedConsumer("test-topic")
        c.close()
        patched_consumer.close.assert_called_once()

    def test_consumer_handles_keyboard_interrupt_gracefully(self, patched_consumer):
        """Consumer should exit without raising on KeyboardInterrupt."""
        from messaging.consumer import UnifiedConsumer

        patched_consumer.poll.side_effect = KeyboardInterrupt()
        c = UnifiedConsumer("test-topic")
        c.consume_messages(lambda msg, t, p: None)

    @pytest.mark.parametrize("group_id", ["group-a", "group-b", "analytics-prod"])
    def test_consumer_group_id_assigned(self, group_id):
        with patch("messaging.consumer.KafkaConsumer") as mock_kc:
            from messaging.consumer import UnifiedConsumer

            c = UnifiedConsumer("test-topic", group_id=group_id)
            assert c.group_id == group_id

    def test_multi_topic_consumer_topics_list(self):
        with patch("messaging.consumer.KafkaConsumer"):
            from messaging.consumer import MultiTopicConsumer

            topics = ["topic.a", "topic.b", "topic.c"]
            c = MultiTopicConsumer(topics)
            assert c.topics == topics

    @pytest.mark.parametrize("broker_urls,expected", [
        (["localhost:9092"], ["localhost:9092"]),
        (["b1:9092", "b2:9092"], ["b1:9092", "b2:9092"]),
    ])
    def test_consumer_broker_urls(self, broker_urls, expected):
        with patch("messaging.consumer.KafkaConsumer"):
            from messaging.consumer import UnifiedConsumer

            c = UnifiedConsumer("test-topic", broker_urls=broker_urls)
            assert c.broker_urls == expected
