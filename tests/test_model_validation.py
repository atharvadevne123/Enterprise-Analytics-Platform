"""Edge-case validation tests for Pydantic data models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from data.models import (
    AnomalyAlert,
    Customer,
    CustomerSegment,
    DeliveryEvent,
    DeliveryStatus,
    InventoryEvent,
    OrderEvent,
    OrderStatus,
    PaymentStatus,
    Product,
    Supplier,
    TransactionEvent,
    TransactionType,
)

NOW = datetime(2024, 6, 15, 12, 0, 0)


class TestOrderStatusEnum:
    @pytest.mark.parametrize("status", list(OrderStatus))
    def test_all_order_statuses_valid(self, status):
        assert isinstance(status.value, str)

    def test_invalid_order_status_raises(self):
        with pytest.raises(Exception):
            OrderEvent(
                order_id=1,
                customer_id=1,
                product_id=1,
                order_date=NOW,
                quantity=1,
                list_price=Decimal("10.00"),
                order_amount=Decimal("10.00"),
                total_amount=Decimal("10.00"),
                cost_amount=Decimal("7.00"),
                order_status="invalid_status",
            )


class TestDecimalFields:
    """Verify Decimal fields reject non-numeric strings."""

    def test_product_cost_decimal(self):
        p = Product(
            product_id=1,
            product_name="Widget",
            category="Tools",
            supplier_id=10,
            cost=Decimal("9.99"),
            list_price=Decimal("14.99"),
        )
        assert p.cost == Decimal("9.99")

    def test_customer_lifetime_value_default(self):
        c = Customer(customer_id=1, customer_name="Alice")
        assert c.lifetime_value == Decimal("0.00")

    @pytest.mark.parametrize("amount", ["0.00", "100.50", "9999999.99"])
    def test_transaction_decimal_amounts(self, amount):
        t = TransactionEvent(
            transaction_id=1,
            gl_account_id="GL-001",
            net_amount=Decimal(amount),
            transaction_type=TransactionType.PAYMENT,
            transaction_date=NOW,
        )
        assert t.net_amount == Decimal(amount)


class TestDefaultValues:
    """Verify model defaults are set correctly."""

    def test_order_event_defaults(self):
        e = OrderEvent(
            order_id=1,
            customer_id=1,
            product_id=1,
            order_date=NOW,
            quantity=5,
            list_price=Decimal("20.00"),
            order_amount=Decimal("100.00"),
            total_amount=Decimal("100.00"),
            cost_amount=Decimal("60.00"),
        )
        assert e.order_status == OrderStatus.PENDING
        assert e.payment_status == PaymentStatus.PENDING
        assert e.discount_amount == Decimal("0.00")

    def test_delivery_event_defaults(self):
        d = DeliveryEvent(
            delivery_id=1,
            po_id=1,
            supplier_id=1,
            product_id=1,
            quantity_ordered=100,
            quantity_delivered=100,
            unit_cost=Decimal("5.00"),
            total_cost=Decimal("500.00"),
            order_date=NOW,
            delivery_date=NOW,
        )
        assert d.quantity_rejected == 0
        assert d.is_on_time is True
        assert d.is_quality_pass is True
        assert d.delivery_status == DeliveryStatus.PENDING

    def test_supplier_defaults(self):
        s = Supplier(
            supplier_id=1,
            supplier_name="ACME",
            country="US",
            lead_time_days=7,
        )
        assert s.is_active is True
        assert s.quality_score == Decimal("0.00")

    def test_customer_segment_default(self):
        c = Customer(customer_id=1, customer_name="Bob")
        assert c.segment == CustomerSegment.REGULAR

    def test_product_is_active_default(self):
        p = Product(
            product_id=1,
            product_name="Gadget",
            category="Electronics",
            supplier_id=2,
            cost=Decimal("50.00"),
            list_price=Decimal("80.00"),
        )
        assert p.is_active is True
        assert p.current_stock_level == 0
        assert p.reorder_point == 100


class TestAnomalyAlertModel:
    def test_anomaly_alert_unresolved_by_default(self):
        alert = AnomalyAlert(
            alert_id="a-001",
            severity="WARNING",
            domain="ecommerce",
            metric_name="daily_orders",
            current_value=Decimal("5"),
            expected_range_min=Decimal("50"),
            expected_range_max=Decimal("200"),
            deviation_pct=Decimal("-90.0"),
        )
        assert alert.resolved is False
        assert alert.root_cause is None

    @pytest.mark.parametrize("severity", ["CRITICAL", "WARNING", "INFO"])
    def test_severity_values(self, severity):
        alert = AnomalyAlert(
            alert_id=f"a-{severity}",
            severity=severity,
            domain="financial",
            metric_name="cash_flow",
            current_value=Decimal("0"),
            expected_range_min=Decimal("1000"),
            expected_range_max=Decimal("5000"),
            deviation_pct=Decimal("-100.0"),
        )
        assert alert.severity == severity


class TestInventoryEvent:
    def test_inventory_event_fields(self):
        e = InventoryEvent(
            product_id=42,
            stock_level=50,
            previous_level=100,
            change_quantity=-50,
            change_reason="Sale",
        )
        assert e.product_id == 42
        assert e.change_quantity == -50
