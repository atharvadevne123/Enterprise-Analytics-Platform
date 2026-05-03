"""Extended Pydantic model validation tests."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from data.models import (
    Customer,
    CustomerSegment,
    DeliveryEvent,
    DeliveryStatus,
    ECommerceMetrics,
    FinancialMetrics,
    OrderEvent,
    OrderStatus,
    PaymentStatus,
    Product,
    SupplyChainMetrics,
)


class TestProductModel:
    def test_valid_product(self):
        p = Product(
            product_id=1,
            product_name="Widget A",
            category="Electronics",
            supplier_id=10,
            cost=Decimal("15.00"),
            list_price=Decimal("29.99"),
        )
        assert p.product_id == 1

    def test_product_id_required(self):
        with pytest.raises(ValidationError):
            Product()

    @pytest.mark.parametrize("category", ["Electronics", "Clothing", "Food", "Furniture"])
    def test_product_categories(self, category):
        p = Product(
            product_id=1,
            product_name="Item",
            category=category,
            supplier_id=1,
            cost=Decimal("5.00"),
            list_price=Decimal("9.99"),
        )
        assert p.category == category


class TestOrderEventModel:
    def test_valid_order_event(self):
        event = OrderEvent(
            order_id=1001,
            customer_id=500,
            product_id=200,
            quantity=3,
            list_price=Decimal("49.99"),
            order_amount=Decimal("149.97"),
            total_amount=Decimal("149.97"),
            cost_amount=Decimal("90.00"),
            order_date=datetime(2024, 1, 15),
        )
        assert event.order_id == 1001

    @pytest.mark.parametrize("status", list(OrderStatus))
    def test_all_order_statuses(self, status):
        event = OrderEvent(
            order_id=1,
            customer_id=1,
            product_id=1,
            quantity=1,
            list_price=Decimal("10.00"),
            order_amount=Decimal("10.00"),
            total_amount=Decimal("10.00"),
            cost_amount=Decimal("6.00"),
            order_date=datetime.now(),
            order_status=status,
        )
        assert event.order_status == status

    @pytest.mark.parametrize("pay_status", list(PaymentStatus))
    def test_all_payment_statuses(self, pay_status):
        event = OrderEvent(
            order_id=1,
            customer_id=1,
            product_id=1,
            quantity=1,
            list_price=Decimal("10.00"),
            order_amount=Decimal("10.00"),
            total_amount=Decimal("10.00"),
            cost_amount=Decimal("6.00"),
            order_date=datetime.now(),
            payment_status=pay_status,
        )
        assert event.payment_status == pay_status


class TestDeliveryEventModel:
    @pytest.mark.parametrize("status", list(DeliveryStatus))
    def test_all_delivery_statuses(self, status):
        event = DeliveryEvent(
            delivery_id=1,
            po_id=100,
            supplier_id=5,
            product_id=10,
            quantity_ordered=10,
            quantity_delivered=10,
            unit_cost=Decimal("5.00"),
            total_cost=Decimal("50.00"),
            order_date=datetime.now(),
            delivery_date=datetime.now(),
            delivery_status=status,
        )
        assert event.delivery_status == status


class TestCustomerModel:
    @pytest.mark.parametrize("segment", list(CustomerSegment))
    def test_all_customer_segments(self, segment):
        c = Customer(
            customer_id=1,
            customer_name="Test User",
            segment=segment,
        )
        assert c.segment == segment

    def test_customer_default_segment(self):
        c = Customer(customer_id=1, customer_name="Test")
        assert c.segment == CustomerSegment.REGULAR

    def test_customer_optional_email(self):
        c = Customer(customer_id=1, customer_name="Test", email="a@b.com")
        assert c.email == "a@b.com"


class TestKPIModels:
    def test_ecommerce_metrics_instantiation(self):
        m = ECommerceMetrics(
            date=datetime(2024, 1, 15),
            total_orders=1200,
            total_customers=850,
            total_revenue=Decimal("95000.50"),
            total_cost=Decimal("60000.00"),
            gross_profit=Decimal("35000.50"),
            average_order_value=Decimal("79.17"),
            conversion_rate=Decimal("3.50"),
            cart_abandonment_rate=Decimal("65.00"),
            inventory_turnover=Decimal("4.20"),
            returned_orders=25,
            refunded_amount=Decimal("1250.00"),
        )
        assert m.total_orders == 1200

    def test_supply_chain_metrics_instantiation(self):
        m = SupplyChainMetrics(
            date=datetime(2024, 1, 15),
            total_deliveries=450,
            on_time_deliveries=425,
            on_time_delivery_pct=Decimal("94.50"),
            total_procurement_cost=Decimal("250000.00"),
            average_lead_time_days=Decimal("3.20"),
            supplier_quality_score=Decimal("87.30"),
        )
        assert m.total_deliveries == 450

    def test_financial_metrics_instantiation(self):
        m = FinancialMetrics(
            date=datetime(2024, 1, 15),
            total_revenue=Decimal("150000.00"),
            total_expense=Decimal("98000.00"),
            net_income=Decimal("52000.00"),
            budget_variance=Decimal("-2000.00"),
            cash_position=Decimal("500000.00"),
            gross_margin_pct=Decimal("34.67"),
        )
        assert m.net_income == Decimal("52000.00")

    @pytest.mark.parametrize("revenue,expense", [
        (Decimal("100000"), Decimal("60000")),
        (Decimal("500000"), Decimal("350000")),
        (Decimal("50000"), Decimal("55000")),
    ])
    def test_financial_metrics_revenue_expense_combinations(self, revenue, expense):
        m = FinancialMetrics(
            date=datetime.now(),
            total_revenue=revenue,
            total_expense=expense,
            net_income=revenue - expense,
            budget_variance=Decimal("0"),
            cash_position=Decimal("100000"),
            gross_margin_pct=Decimal("30.00"),
        )
        assert m.total_revenue == revenue
