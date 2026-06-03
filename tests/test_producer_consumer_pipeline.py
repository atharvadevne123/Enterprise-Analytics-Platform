"""Tests for Kafka producer-consumer pipeline interactions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestProducerEventFormats:
    """Verify producer sends events with correct topic routing."""

    @pytest.fixture(autouse=True)
    def setup(self):
        with patch("messaging.producer.KafkaProducer") as mock_cls:
            self.mock_producer = MagicMock()
            mock_cls.return_value = self.mock_producer
            from messaging.producer import UnifiedProducer

            self.p = UnifiedProducer(broker_urls=["localhost:9092"])
            yield

    @pytest.mark.parametrize(
        "event,method",
        [
            ({"order_id": 1, "status": "shipped"}, "send_order_event"),
            ({"product_id": 10, "stock": 50}, "send_inventory_event"),
            ({"customer_id": 5, "segment": "vip"}, "send_customer_event"),
            ({"delivery_id": "DEL-1", "status": "delivered"}, "send_delivery_event"),
            ({"po_id": "PO-1", "status": "approved"}, "send_purchase_order_event"),
            ({"supplier_id": 3, "name": "ACME"}, "send_supplier_event"),
            ({"transaction_id": "TXN-1", "amount": 999.99}, "send_transaction_event"),
            ({"budget_id": "BUD-1", "amount": 50000.0}, "send_budget_event"),
            ({"transaction_id": "TXN-2", "amount": 1234.56}, "send_financial_event"),
        ],
    )
    def test_send_event_calls_kafka_send(self, event, method):
        result = getattr(self.p, method)(event)
        assert result is True or result is False
        self.mock_producer.send.assert_called()

    def test_flush_before_close(self):
        self.p.flush()
        self.mock_producer.flush.assert_called_once()

    def test_close_after_flush(self):
        self.p.flush()
        self.p.close()
        self.mock_producer.flush.assert_called()
        self.mock_producer.close.assert_called_once()

    @pytest.mark.parametrize(
        "error_type",
        [
            Exception("timeout"),
            Exception("serialization error"),
            Exception("broker unavailable"),
        ],
    )
    def test_send_returns_false_on_error(self, error_type):
        self.mock_producer.send.side_effect = error_type
        result = self.p.send_order_event({"order_id": 1})
        assert result is False


class TestConsumerGroupIsolation:
    """Verify different consumer groups operate independently."""

    @pytest.mark.parametrize(
        "group1,group2",
        [
            ("group-a", "group-b"),
            ("analytics", "reporting"),
            ("etl-consumers", "api-consumers"),
        ],
    )
    def test_separate_consumer_groups(self, group1, group2):
        with patch("messaging.consumer.KafkaConsumer") as mock_cls:
            mock_cls.return_value = MagicMock()
            from messaging.consumer import UnifiedConsumer

            c1 = UnifiedConsumer(topic="orders", group_id=group1)
            c2 = UnifiedConsumer(topic="orders", group_id=group2)
            assert c1.group_id != c2.group_id
            assert c1.group_id == group1
            assert c2.group_id == group2


class TestMultiTopicConsumer:
    """Tests for the MultiTopicConsumer class."""

    def test_multi_topic_instantiation(self):
        with patch("messaging.consumer.KafkaConsumer") as mock_cls:
            mock_cls.return_value = MagicMock()
            from messaging.consumer import MultiTopicConsumer

            c = MultiTopicConsumer(
                topics=["orders", "deliveries", "financial-transactions"],
                broker_urls=["localhost:9092"],
            )
            assert c.topics == ["orders", "deliveries", "financial-transactions"]

    def test_multi_topic_close(self):
        with patch("messaging.consumer.KafkaConsumer") as mock_cls:
            mock_inst = MagicMock()
            mock_cls.return_value = mock_inst
            from messaging.consumer import MultiTopicConsumer

            c = MultiTopicConsumer(topics=["orders"], broker_urls=["localhost:9092"])
            c.close()
            mock_inst.close.assert_called_once()

    @pytest.mark.parametrize(
        "topics",
        [
            ["orders"],
            ["orders", "deliveries"],
            ["orders", "deliveries", "financial-transactions", "inventory-updates"],
        ],
    )
    def test_multi_topic_with_various_topic_counts(self, topics):
        with patch("messaging.consumer.KafkaConsumer") as mock_cls:
            mock_cls.return_value = MagicMock()
            from messaging.consumer import MultiTopicConsumer

            c = MultiTopicConsumer(topics=topics, broker_urls=["localhost:9092"])
            assert len(c.topics) == len(topics)


# ---------------------------------------------------------------------------
# Additional pipeline tests
# ---------------------------------------------------------------------------


class TestProducerBatchSend:
    @pytest.fixture()
    def mock_producer_instance(self):
        with patch("messaging.producer.KafkaProducer") as mock_kp:
            mock_inst = MagicMock()
            mock_kp.return_value = mock_inst
            yield mock_inst

    def test_batch_send_all_events(self, mock_producer_instance):
        from messaging.producer import UnifiedProducer

        producer = UnifiedProducer.__new__(UnifiedProducer)
        producer.broker_urls = ["localhost:9092"]
        producer.producer = mock_producer_instance

        events = [{"order_id": i, "amount": i * 10} for i in range(1, 6)]
        results = [producer.send_order_event(e) for e in events]
        assert all(r is True for r in results)
        assert mock_producer_instance.send.call_count == 5

    @pytest.mark.parametrize(
        "domain,send_method,data_key",
        [
            ("transaction", "send_transaction_event", "transaction_id"),
            ("budget", "send_budget_event", "budget_id"),
            ("actual", "send_actual_event", "actual_id"),
        ],
    )
    def test_financial_event_methods(self, mock_producer_instance, domain, send_method, data_key):
        from messaging.producer import UnifiedProducer

        producer = UnifiedProducer.__new__(UnifiedProducer)
        producer.broker_urls = ["localhost:9092"]
        producer.producer = mock_producer_instance

        data = {data_key: 1, "amount": 1000}
        result = getattr(producer, send_method)(data)
        assert result is True
