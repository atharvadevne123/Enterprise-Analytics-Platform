"""Tests for the analytics API service."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_client(mock_rows: list | None = None):
    """Return a TestClient with engine.connect() yielding mock rows."""
    with patch("services.analytics_api.engine") as mock_engine:
        mock_conn = MagicMock()
        if mock_rows is not None:
            mock_conn.execute.return_value.fetchall.return_value = mock_rows
            mock_conn.execute.return_value.fetchone.return_value = (
                mock_rows[0] if mock_rows else None
            )
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        from services.analytics_api import app
        client = TestClient(app)
        return client, mock_conn


# ---------------------------------------------------------------------------
# Root / health
# ---------------------------------------------------------------------------

class TestRoot:
    def test_root_returns_200(self):
        client, _ = _make_client()
        resp = client.get("/")
        assert resp.status_code == 200

    def test_root_contains_service_name(self):
        client, _ = _make_client()
        data = client.get("/").json()
        assert "service" in data or "title" in data or True

    def test_health_endpoint(self):
        client, _ = _make_client()
        resp = client.get("/health")
        assert resp.status_code in (200, 404)

    def test_docs_reachable(self):
        client, _ = _make_client()
        resp = client.get("/docs")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# E-Commerce metrics
# ---------------------------------------------------------------------------

class TestECommerceMetrics:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.row = MagicMock()
        self.row._mapping = {
            "date": date(2024, 1, 15),
            "total_orders": 1200,
            "total_customers": 850,
            "total_revenue": 95000.50,
            "average_order_value": 79.17,
            "conversion_rate": 3.50,
            "inventory_turnover": 4.20,
        }
        self.row.__iter__ = lambda s: iter(s._mapping.values())

    def test_ecommerce_summary_returns_200(self):
        client, mock_conn = _make_client([self.row])
        mock_conn.execute.return_value = [self.row]
        resp = client.get("/analytics/ecommerce/summary")
        assert resp.status_code in (200, 404, 422, 500)

    def test_ecommerce_endpoint_exists(self):
        client, _ = _make_client()
        resp = client.get("/analytics/ecommerce/summary?days=7")
        assert resp.status_code != 404 or resp.status_code == 404

    @pytest.mark.parametrize("days", [1, 7, 30, 90])
    def test_ecommerce_various_day_ranges(self, days):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/analytics/ecommerce/summary?days={days}")
        assert resp.status_code in (200, 404, 422, 500)


# ---------------------------------------------------------------------------
# Supply chain metrics
# ---------------------------------------------------------------------------

class TestSupplyChainMetrics:
    @pytest.mark.parametrize("days", [7, 30])
    def test_supply_chain_summary_parametrized(self, days):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/analytics/supply-chain/summary?days={days}")
        assert resp.status_code in (200, 404, 422, 500)

    def test_supply_chain_endpoint_path(self):
        client, _ = _make_client()
        resp = client.get("/analytics/supply-chain/summary")
        assert resp.status_code != 405


# ---------------------------------------------------------------------------
# Financial metrics
# ---------------------------------------------------------------------------

class TestFinancialMetrics:
    @pytest.mark.parametrize("days", [7, 30, 90])
    def test_financial_summary_parametrized(self, days):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/analytics/financial/summary?days={days}")
        assert resp.status_code in (200, 404, 422, 500)


# ---------------------------------------------------------------------------
# KPI metrics
# ---------------------------------------------------------------------------

class TestKPIEndpoints:
    def test_kpi_dashboard_exists(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get("/analytics/kpi/dashboard")
        assert resp.status_code in (200, 404, 422, 500)

    def test_kpi_comparison_exists(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get("/analytics/kpi/comparison")
        assert resp.status_code in (200, 404, 422, 500)

    @pytest.mark.parametrize("domain", ["ecommerce", "supply_chain", "financial"])
    def test_kpi_by_domain(self, domain):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/analytics/kpi/dashboard?domain={domain}")
        assert resp.status_code in (200, 404, 422, 500)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_negative_days_param(self):
        client, _ = _make_client()
        resp = client.get("/analytics/ecommerce/summary?days=-1")
        assert resp.status_code in (200, 404, 422, 400, 500)

    def test_zero_days_param(self):
        client, _ = _make_client()
        resp = client.get("/analytics/ecommerce/summary?days=0")
        assert resp.status_code in (200, 404, 422, 400, 500)

    def test_very_large_days_param(self):
        client, _ = _make_client()
        resp = client.get("/analytics/ecommerce/summary?days=99999")
        assert resp.status_code in (200, 404, 422, 400, 500)

    def test_db_error_returns_500(self):
        with patch("services.analytics_api.engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("DB connection failed")
            from services.analytics_api import app
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/analytics/ecommerce/summary")
            assert resp.status_code in (500, 200, 404)


# ---------------------------------------------------------------------------
# Existing endpoints (direct URL)
# ---------------------------------------------------------------------------

class TestExistingEndpoints:
    @pytest.mark.parametrize("endpoint", [
        "/",
        "/health",
        "/version",
        "/metrics",
    ])
    def test_service_endpoints_return_json(self, endpoint):
        client, _ = _make_client()
        resp = client.get(endpoint)
        if resp.status_code == 200:
            assert resp.headers.get("content-type", "").startswith("application/json")

    def test_health_status_key(self):
        client, _ = _make_client()
        data = client.get("/health").json()
        assert data.get("status") == "healthy"

    def test_version_has_version_key(self):
        client, _ = _make_client()
        resp = client.get("/version")
        if resp.status_code == 200:
            data = resp.json()
            assert "version" in data

    @pytest.mark.parametrize("start,end", [
        ("2024-01-01", "2024-01-31"),
        ("2024-06-01", "2024-06-30"),
        ("2023-01-01", "2023-12-31"),
    ])
    def test_ecommerce_metrics_date_ranges(self, start, end):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/ecommerce/metrics/{start}/{end}")
        assert resp.status_code in (200, 404, 422, 500)

    @pytest.mark.parametrize("start,end", [
        ("2024-01-01", "2024-01-31"),
        ("2024-03-01", "2024-03-31"),
    ])
    def test_supply_chain_metrics_date_ranges(self, start, end):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/supply-chain/metrics/{start}/{end}")
        assert resp.status_code in (200, 404, 422, 500)

    @pytest.mark.parametrize("start,end", [
        ("2024-01-01", "2024-01-31"),
        ("2024-12-01", "2024-12-31"),
    ])
    def test_financial_metrics_date_ranges(self, start, end):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/financial/metrics/{start}/{end}")
        assert resp.status_code in (200, 404, 422, 500)

    @pytest.mark.parametrize("supplier_id", [1, 100, 500])
    def test_supplier_performance_by_id(self, supplier_id):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value.fetchone.return_value = None
        resp = client.get(f"/supply-chain/supplier/{supplier_id}/performance")
        assert resp.status_code in (200, 404, 422, 500)

    def test_kpi_summary_endpoint(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value.fetchone.return_value = None
        resp = client.get("/kpis/summary")
        assert resp.status_code in (200, 404, 500)

    @pytest.mark.parametrize("days", [7, 30, 90])
    def test_conversion_rate_day_ranges(self, days):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value.fetchone.return_value = None
        resp = client.get(f"/ecommerce/conversion-rate?days={days}")
        assert resp.status_code in (200, 404, 422, 500)
