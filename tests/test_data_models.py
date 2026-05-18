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


class TestProductModel:
    """Unit tests for the Product Pydantic model."""

    def test_product_requires_product_id(self):
        from data.models import Product
        from decimal import Decimal
        p = Product(
            product_id=1,
            product_name="Widget",
            category="hardware",
            supplier_id=10,
            cost=Decimal("5.00"),
            list_price=Decimal("9.99"),
        )
        assert p.product_id == 1

    def test_product_defaults_active_true(self):
        from data.models import Product
        from decimal import Decimal
        p = Product(
            product_id=2, product_name="Gadget", category="electronics",
            supplier_id=1, cost=Decimal("10"), list_price=Decimal("25"),
        )
        assert p.is_active is True

    def test_product_default_stock_zero(self):
        from data.models import Product
        from decimal import Decimal
        p = Product(
            product_id=3, product_name="Tool", category="tools",
            supplier_id=2, cost=Decimal("3"), list_price=Decimal("7"),
        )
        assert p.current_stock_level == 0


class TestOrderEventModel:
    """Unit tests for the OrderEvent Pydantic model."""

    def _make_order(self, **overrides):
        from datetime import datetime
        from decimal import Decimal
        from data.models import OrderEvent
        base = dict(
            order_id=1, customer_id=10, product_id=100,
            order_date=datetime(2024, 1, 15, 12, 0),
            quantity=2, list_price=Decimal("50.00"),
            order_amount=Decimal("100.00"),
            total_amount=Decimal("110.00"),
            cost_amount=Decimal("40.00"),
        )
        base.update(overrides)
        return OrderEvent(**base)

    def test_order_default_status_pending(self):
        from data.models import OrderStatus
        order = self._make_order()
        assert order.order_status == OrderStatus.PENDING

    def test_order_default_payment_pending(self):
        from data.models import PaymentStatus
        order = self._make_order()
        assert order.payment_status == PaymentStatus.PENDING

    def test_order_discount_defaults_zero(self):
        from decimal import Decimal
        order = self._make_order()
        assert order.discount_amount == Decimal("0.00")

    @pytest.mark.parametrize("quantity", [1, 5, 100, 1000])
    def test_order_various_quantities(self, quantity):
        order = self._make_order(quantity=quantity)
        assert order.quantity == quantity


class TestCustomerModel:
    """Unit tests for the Customer Pydantic model."""

    def _make_customer(self, **overrides):
        from datetime import datetime
        from data.models import Customer
        base = dict(customer_id=1, customer_name="Alice")
        base.update(overrides)
        return Customer(**base)

    def test_customer_default_segment_regular(self):
        from data.models import CustomerSegment
        c = self._make_customer()
        assert c.segment == CustomerSegment.REGULAR

    @pytest.mark.parametrize("segment_val", ["vip", "regular", "new", "inactive"])
    def test_customer_segment_enum_assignment(self, segment_val):
        from data.models import CustomerSegment
        c = self._make_customer(segment=CustomerSegment(segment_val))
        assert c.segment.value == segment_val
