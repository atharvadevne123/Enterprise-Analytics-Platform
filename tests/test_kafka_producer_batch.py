"""Additional tests for UnifiedProducer send_batch method."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, call, patch

import pytest

from data.models import OrderEvent, OrderStatus, PaymentStatus
from datetime import datetime


NOW = datetime(2024, 6, 15, 12, 0, 0)


def _make_order(order_id: int) -> OrderEvent:
    return OrderEvent(
        order_id=order_id,
        customer_id=1,
        product_id=1,
        order_date=NOW,
        quantity=2,
        list_price=Decimal("10.00"),
        order_amount=Decimal("20.00"),
        total_amount=Decimal("20.00"),
        cost_amount=Decimal("14.00"),
    )


class TestSendBatchMethod:
    @patch("messaging.producer.KafkaProducer")
    def test_send_batch_returns_queued_count(self, mock_kafka):
        mock_producer = MagicMock()
        mock_kafka.return_value = mock_producer

        from messaging.producer import UnifiedProducer
        p = UnifiedProducer()

        events = [_make_order(i) for i in range(5)]
        count = p.send_batch("ecommerce.orders", events)
        assert count == 5

    @patch("messaging.producer.KafkaProducer")
    def test_send_batch_uses_key_field(self, mock_kafka):
        mock_producer = MagicMock()
        mock_kafka.return_value = mock_producer

        from messaging.producer import UnifiedProducer
        p = UnifiedProducer()

        events = [_make_order(i) for i in range(3)]
        p.send_batch("ecommerce.orders", events, key_field="order_id")
        assert mock_producer.send.call_count == 3

    @patch("messaging.producer.KafkaProducer")
    def test_send_batch_empty_list(self, mock_kafka):
        mock_producer = MagicMock()
        mock_kafka.return_value = mock_producer

        from messaging.producer import UnifiedProducer
        p = UnifiedProducer()
        count = p.send_batch("ecommerce.orders", [])
        assert count == 0

    @patch("messaging.producer.KafkaProducer")
    def test_send_batch_handles_send_failure(self, mock_kafka):
        mock_producer = MagicMock()
        mock_producer.send.side_effect = Exception("Kafka unavailable")
        mock_kafka.return_value = mock_producer

        from messaging.producer import UnifiedProducer
        p = UnifiedProducer()
        events = [_make_order(i) for i in range(3)]
        count = p.send_batch("ecommerce.orders", events)
        assert count == 0

    @patch("messaging.producer.KafkaProducer")
    def test_send_batch_dict_events(self, mock_kafka):
        mock_producer = MagicMock()
        mock_kafka.return_value = mock_producer

        from messaging.producer import UnifiedProducer
        p = UnifiedProducer()
        events = [{"order_id": i, "amount": 100.0} for i in range(4)]
        count = p.send_batch("test.topic", events)
        assert count == 4

    @pytest.mark.parametrize("batch_size", [1, 10, 50, 100])
    @patch("messaging.producer.KafkaProducer")
    def test_send_batch_various_sizes(self, mock_kafka, batch_size):
        mock_producer = MagicMock()
        mock_kafka.return_value = mock_producer

        from messaging.producer import UnifiedProducer
        p = UnifiedProducer()
        events = [_make_order(i) for i in range(batch_size)]
        count = p.send_batch("ecommerce.orders", events)
        assert count == batch_size
