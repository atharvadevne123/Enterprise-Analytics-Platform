"""Tests for Pydantic data models."""

from __future__ import annotations

import pytest

from data.models import (
    CustomerSegment,
    DeliveryStatus,
    OrderStatus,
    PaymentStatus,
    TransactionType,
)


class TestEnums:
    @pytest.mark.parametrize("status", ["pending", "shipped", "delivered", "cancelled", "returned"])
    def test_order_status_valid_values(self, status):
        assert OrderStatus(status) is not None

    def test_order_status_invalid_raises(self):
        with pytest.raises(ValueError):
            OrderStatus("invalid_status")

    @pytest.mark.parametrize("status", ["pending", "paid", "failed", "refunded"])
    def test_payment_status_valid_values(self, status):
        assert PaymentStatus(status) is not None

    def test_payment_status_invalid_raises(self):
        with pytest.raises(ValueError):
            PaymentStatus("unknown")

    @pytest.mark.parametrize("status", ["pending", "in_transit", "delivered", "delayed", "cancelled"])
    def test_delivery_status_valid_values(self, status):
        assert DeliveryStatus(status) is not None

    @pytest.mark.parametrize("txn_type", ["journal_entry", "invoice", "payment", "credit_memo", "debit_memo"])
    def test_transaction_type_valid_values(self, txn_type):
        assert TransactionType(txn_type) is not None

    @pytest.mark.parametrize("segment", ["vip", "regular", "new", "inactive"])
    def test_customer_segment_valid_values(self, segment):
        assert CustomerSegment(segment) is not None


class TestOrderStatusTransitions:
    def test_pending_is_string(self):
        assert str(OrderStatus.PENDING) == "OrderStatus.PENDING" or OrderStatus.PENDING.value == "pending"

    def test_all_statuses_iterable(self):
        statuses = list(OrderStatus)
        assert len(statuses) == 5

    def test_all_payment_statuses_iterable(self):
        statuses = list(PaymentStatus)
        assert len(statuses) == 4

    def test_all_customer_segments_iterable(self):
        segments = list(CustomerSegment)
        assert len(segments) == 4


class TestModelImports:
    def test_import_order_status(self):
        from data.models import OrderStatus
        assert OrderStatus is not None

    def test_import_product_model(self):
        from data.models import Product
        assert Product is not None

    def test_import_order_event(self):
        from data.models import OrderEvent
        assert OrderEvent is not None

    def test_import_delivery_event(self):
        from data.models import DeliveryEvent
        assert DeliveryEvent is not None

    def test_import_transaction_event(self):
        from data.models import TransactionEvent
        assert TransactionEvent is not None
