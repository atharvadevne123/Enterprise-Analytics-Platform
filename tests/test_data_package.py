"""Tests for the data models package public interface."""

from __future__ import annotations

import pytest


class TestDataModelsImport:
    @pytest.mark.parametrize("model_name", [
        "Product",
        "Customer",
        "OrderEvent",
        "InventoryEvent",
        "Supplier",
        "PurchaseOrderEvent",
        "DeliveryEvent",
        "GLAccount",
        "TransactionEvent",
        "BudgetEvent",
        "ActualEvent",
    ])
    def test_all_models_importable(self, model_name):
        import data.models as models

        cls = getattr(models, model_name)
        assert cls is not None

    @pytest.mark.parametrize("enum_name", [
        "OrderStatus",
        "PaymentStatus",
        "DeliveryStatus",
        "TransactionType",
        "CustomerSegment",
    ])
    def test_all_enums_importable(self, enum_name):
        import data.models as models

        enum = getattr(models, enum_name)
        assert enum is not None

    def test_base_analytics_model_importable(self):
        from data.models import BaseAnalyticsModel

        assert BaseAnalyticsModel is not None


class TestDataModelsInheritance:
    @pytest.mark.parametrize("model_name", [
        "Product",
        "Customer",
        "OrderEvent",
        "Supplier",
        "GLAccount",
        "TransactionEvent",
    ])
    def test_model_inherits_base_analytics_model(self, model_name):
        import data.models as models
        from data.models import BaseAnalyticsModel

        cls = getattr(models, model_name)
        assert issubclass(cls, BaseAnalyticsModel)

    def test_kpi_models_importable(self):
        from data.models import ECommerceMetrics, FinancialMetrics, SupplyChainMetrics, UnifiedKPIMetrics

        for cls in [ECommerceMetrics, FinancialMetrics, SupplyChainMetrics, UnifiedKPIMetrics]:
            assert cls is not None

    def test_forecast_models_importable(self):
        from data.models import CashFlowForecast, DemandForecast, LeadTimeForecast

        for cls in [DemandForecast, LeadTimeForecast, CashFlowForecast]:
            assert cls is not None
