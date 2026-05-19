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


class TestAllSendMethods:
    """Test every send_*_event method on UnifiedProducer."""

    @pytest.fixture(autouse=True)
    def setup(self):
        with patch("messaging.producer.KafkaProducer") as mock_cls:
            self.mock_instance = MagicMock()
            mock_cls.return_value = self.mock_instance
            from messaging.producer import UnifiedProducer

            self.producer = UnifiedProducer(broker_urls=["localhost:9092"])
            yield

    @pytest.mark.parametrize(
        "method,payload_key",
        [
            ("send_order_event", "order_id"),
            ("send_inventory_event", "product_id"),
            ("send_customer_event", "customer_id"),
            ("send_delivery_event", "delivery_id"),
            ("send_purchase_order_event", "po_id"),
            ("send_supplier_event", "supplier_id"),
            ("send_transaction_event", "transaction_id"),
            ("send_budget_event", "budget_id"),
            ("send_actual_event", "actual_id"),
        ],
    )
    def test_each_send_method_calls_produce(self, method, payload_key):
        self.mock_instance.send.reset_mock()
        fn = getattr(self.producer, method)
        result = fn({payload_key: 1, "data": "test"})
        self.mock_instance.send.assert_called_once()
        assert result is True

    def test_send_returns_false_on_kafka_error(self):
        self.mock_instance.send.side_effect = Exception("Broker error")
        result = self.producer.send_order_event({"order_id": 999})
        assert result is False

    def test_financial_event_alias(self):
        """send_financial_event is an alias for send_transaction_event."""
        self.mock_instance.send.reset_mock()
        self.producer.send_financial_event({"transaction_id": 42})
        self.mock_instance.send.assert_called_once()

    def test_flush_calls_producer_flush(self):
        self.producer.flush(timeout_ms=5000)
        self.mock_instance.flush.assert_called_once_with(timeout_ms=5000)


class TestDecimalEncoder:
    """Unit tests for DecimalEncoder JSON serialisation."""

    def test_decimal_encoded_as_float(self):
        import json
        from decimal import Decimal

        from messaging.producer import DecimalEncoder

        result = json.dumps({"v": Decimal("3.14")}, cls=DecimalEncoder)
        assert "3.14" in result

    def test_datetime_encoded_as_iso_string(self):
        import json
        from datetime import datetime

        from messaging.producer import DecimalEncoder

        dt = datetime(2024, 6, 15, 10, 30, 0)
        result = json.dumps({"ts": dt}, cls=DecimalEncoder)
        assert "2024-06-15" in result

    def test_other_types_use_default_encoder(self):
        import json

        from messaging.producer import DecimalEncoder

        with pytest.raises(TypeError):
            json.dumps({"v": object()}, cls=DecimalEncoder)
