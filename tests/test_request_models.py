"""Tests for new request models: ForecastConfig, AnomalyDetectionConfig, DateRangeFilter."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from data.models import AnomalyDetectionConfig, DateRangeFilter, ForecastConfig

NOW = datetime(2024, 6, 15, 12, 0, 0)
LATER = datetime(2024, 7, 15, 12, 0, 0)


class TestForecastConfig:
    def test_defaults(self):
        fc = ForecastConfig()
        assert fc.horizon_days == 30
        assert fc.model_type == "linear_regression"
        assert fc.include_bounds is True
        assert fc.product_id is None
        assert fc.supplier_id is None

    @pytest.mark.parametrize("horizon", [1, 30, 90, 180, 365])
    def test_valid_horizon_days(self, horizon):
        fc = ForecastConfig(horizon_days=horizon)
        assert fc.horizon_days == horizon

    def test_invalid_horizon_too_low(self):
        with pytest.raises(Exception):
            ForecastConfig(horizon_days=0)

    def test_invalid_horizon_too_high(self):
        with pytest.raises(Exception):
            ForecastConfig(horizon_days=366)

    def test_with_product_id(self):
        fc = ForecastConfig(product_id=42, horizon_days=60)
        assert fc.product_id == 42

    def test_confidence_threshold_decimal(self):
        fc = ForecastConfig(confidence_threshold=Decimal("0.85"))
        assert fc.confidence_threshold == Decimal("0.85")


class TestAnomalyDetectionConfig:
    def test_defaults(self):
        cfg = AnomalyDetectionConfig(metric_name="daily_orders", domain="ecommerce")
        assert cfg.method == "zscore"
        assert cfg.lookback_days == 30
        assert cfg.alert_on_detect is True

    @pytest.mark.parametrize("domain", ["ecommerce", "supply_chain", "financial"])
    def test_valid_domains(self, domain):
        cfg = AnomalyDetectionConfig(metric_name="test_metric", domain=domain)
        assert cfg.domain == domain

    def test_invalid_lookback_too_low(self):
        with pytest.raises(Exception):
            AnomalyDetectionConfig(metric_name="x", domain="ecommerce", lookback_days=3)

    def test_invalid_lookback_too_high(self):
        with pytest.raises(Exception):
            AnomalyDetectionConfig(metric_name="x", domain="ecommerce", lookback_days=400)

    def test_custom_sensitivity(self):
        cfg = AnomalyDetectionConfig(
            metric_name="revenue",
            domain="financial",
            sensitivity=Decimal("3.0"),
        )
        assert cfg.sensitivity == Decimal("3.0")


class TestDateRangeFilter:
    def test_defaults(self):
        drf = DateRangeFilter(start_date=NOW, end_date=LATER)
        assert drf.granularity == "daily"
        assert drf.limit == 100
        assert drf.offset == 0

    @pytest.mark.parametrize("limit", [1, 50, 100, 500, 1000])
    def test_valid_limits(self, limit):
        drf = DateRangeFilter(start_date=NOW, end_date=LATER, limit=limit)
        assert drf.limit == limit

    def test_invalid_limit_zero(self):
        with pytest.raises(Exception):
            DateRangeFilter(start_date=NOW, end_date=LATER, limit=0)

    def test_invalid_limit_over_max(self):
        with pytest.raises(Exception):
            DateRangeFilter(start_date=NOW, end_date=LATER, limit=1001)

    def test_negative_offset_raises(self):
        with pytest.raises(Exception):
            DateRangeFilter(start_date=NOW, end_date=LATER, offset=-1)


# ---------------------------------------------------------------------------
# Additional request model tests
# ---------------------------------------------------------------------------


class TestDateRangeRequestModel:
    def test_date_range_request_valid(self):
        from datetime import date

        from services.analytics_api import DateRangeRequest

        req = DateRangeRequest(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
        assert req.start_date < req.end_date

    def test_date_range_request_same_day(self):
        from datetime import date

        from services.analytics_api import DateRangeRequest

        req = DateRangeRequest(start_date=date(2024, 6, 15), end_date=date(2024, 6, 15))
        assert req.start_date == req.end_date

    def test_date_range_request_end_before_start_raises(self):
        from datetime import date

        from services.analytics_api import DateRangeRequest

        with pytest.raises(Exception):
            DateRangeRequest(start_date=date(2024, 12, 31), end_date=date(2024, 1, 1))

    @pytest.mark.parametrize("start,end", [
        ("2024-01-01", "2024-03-31"),
        ("2023-06-01", "2023-09-30"),
        ("2024-12-01", "2024-12-31"),
    ])
    def test_date_range_various_valid_ranges(self, start, end):
        from datetime import date

        from services.analytics_api import DateRangeRequest

        s = date.fromisoformat(start)
        e = date.fromisoformat(end)
        req = DateRangeRequest(start_date=s, end_date=e)
        assert req.end_date >= req.start_date
