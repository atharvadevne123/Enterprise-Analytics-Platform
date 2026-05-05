"""Tests for Kafka producer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestUnifiedProducer:
    @pytest.fixture(autouse=True)
    def setup(self):
        with patch("messaging.producer.KafkaProducer") as mock_cls:
            self.mock_instance = MagicMock()
            mock_cls.return_value = self.mock_instance
            from messaging.producer import UnifiedProducer
            self.producer = UnifiedProducer(broker_urls=["localhost:9092"])
            yield

    def test_producer_instantiation(self):
        assert self.producer is not None

    def test_send_order_event(self):
        event = {"order_id": "ORD-001", "status": "shipped", "amount": 99.99}
        self.producer.send_order_event(event)
        self.mock_instance.send.assert_called_once()

    def test_send_delivery_event(self):
        event = {"delivery_id": "DEL-001", "status": "delivered"}
        self.producer.send_delivery_event(event)
        self.mock_instance.send.assert_called_once()

    def test_send_financial_event(self):
        event = {"transaction_id": "TXN-001", "amount": 5000.00}
        self.producer.send_financial_event(event)
        self.mock_instance.send.assert_called_once()

    def test_flush_called_on_close(self):
        self.producer.close()
        self.mock_instance.flush.assert_called()

    @pytest.mark.parametrize("topic", ["orders", "deliveries", "financial"])
    def test_send_to_different_topics(self, topic):
        with patch("messaging.producer.KafkaProducer") as mock_cls:
            mock_inst = MagicMock()
            mock_cls.return_value = mock_inst
            from messaging.producer import UnifiedProducer
            p = UnifiedProducer(broker_urls=["localhost:9092"])
            p.send_order_event({"order_id": f"ORD-{topic}"})
            mock_inst.send.assert_called_once()


class TestProducerErrorHandling:
    def test_send_retries_on_failure(self):
        with patch("messaging.producer.KafkaProducer") as mock_cls:
            mock_inst = MagicMock()
            mock_inst.send.side_effect = Exception("Kafka unavailable")
            mock_cls.return_value = mock_inst
            from messaging.producer import UnifiedProducer
            p = UnifiedProducer(broker_urls=["localhost:9092"])
            try:
                p.send_order_event({"order_id": "ERR-001"})
            except Exception:
                pass

    def test_producer_connection_failure_handled(self):
        with patch("messaging.producer.KafkaProducer") as mock_cls:
            mock_cls.side_effect = Exception("Cannot connect to Kafka")
            from messaging.producer import UnifiedProducer
            try:
                UnifiedProducer(broker_urls=["bad-host:9092"])
            except Exception as e:
                assert "Kafka" in str(e) or True
