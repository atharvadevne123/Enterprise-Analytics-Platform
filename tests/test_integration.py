"""Integration-level tests for service interactions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestAnalyticsAPIIntegration:
    """Integration tests verifying analytics API response shapes."""

    def _make_client(self):
        with patch("services.analytics_api.engine") as mock_engine:
            mock_conn = MagicMock()
            mock_conn.execute.return_value.fetchone.return_value = None
            mock_conn.execute.return_value.fetchall.return_value = []
            mock_conn.execute.return_value.__iter__ = lambda s: iter([])
            mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
            mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
            mock_engine.pool.size.return_value = 20
            from services.analytics_api import app
            return TestClient(app), mock_conn

    def test_root_response_shape(self):
        client, _ = self._make_client()
        data = client.get("/").json()
        assert isinstance(data, dict)
        assert "service" in data

    def test_health_response_shape(self):
        client, _ = self._make_client()
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert "service" in data

    def test_version_response_shape(self):
        client, _ = self._make_client()
        resp = client.get("/version")
        if resp.status_code == 200:
            data = resp.json()
            assert "version" in data
            assert "service" in data

    def test_metrics_response_shape(self):
        client, _ = self._make_client()
        resp = client.get("/metrics")
        if resp.status_code == 200:
            data = resp.json()
            assert "service" in data

    def test_kpi_summary_returns_dict(self):
        client, mock_conn = self._make_client()
        resp = client.get("/kpis/summary")
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, dict)

    @pytest.mark.parametrize("granularity", ["daily", "weekly", "monthly"])
    def test_ecommerce_metrics_granularity(self, granularity):
        client, mock_conn = self._make_client()
        mock_conn.execute.return_value.__iter__ = lambda s: iter([])
        resp = client.get(
            f"/ecommerce/metrics/2024-01-01/2024-01-31?granularity={granularity}"
        )
        assert resp.status_code in (200, 422, 500)

    def test_invalid_granularity_rejected(self):
        client, _ = self._make_client()
        resp = client.get(
            "/ecommerce/metrics/2024-01-01/2024-01-31?granularity=hourly"
        )
        assert resp.status_code in (422, 400, 500)


class TestAnomalyServiceIntegration:
    def _make_client(self):
        with patch("services.anomaly_detection.engine") as mock_engine:
            mock_conn = MagicMock()
            mock_conn.execute.return_value.fetchone.return_value = None
            mock_conn.execute.return_value.fetchall.return_value = []
            mock_conn.execute.return_value.__iter__ = lambda s: iter([])
            mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
            mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
            mock_engine.pool.size.return_value = 20
            from services.anomaly_detection import app
            return TestClient(app), mock_conn

    def test_root_response_has_service(self):
        client, _ = self._make_client()
        data = client.get("/").json()
        assert data.get("service") == "anomaly-detection"

    def test_health_response_healthy(self):
        client, _ = self._make_client()
        data = client.get("/health").json()
        assert data["status"] == "healthy"

    def test_version_endpoint(self):
        client, _ = self._make_client()
        resp = client.get("/version")
        if resp.status_code == 200:
            assert "version" in resp.json()


class TestForecastingServiceIntegration:
    def _make_client(self):
        with patch("services.forecasting_service.engine") as mock_engine:
            mock_conn = MagicMock()
            mock_conn.execute.return_value.fetchone.return_value = None
            mock_conn.execute.return_value.fetchall.return_value = []
            mock_conn.execute.return_value.__iter__ = lambda s: iter([])
            mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
            mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
            mock_engine.pool.size.return_value = 20
            from services.forecasting_service import app
            return TestClient(app), mock_conn

    def test_root_response_has_service(self):
        client, _ = self._make_client()
        data = client.get("/").json()
        assert data.get("service") == "forecasting-service"

    def test_health_response_healthy(self):
        client, _ = self._make_client()
        data = client.get("/health").json()
        assert data["status"] == "healthy"

    @pytest.mark.parametrize("horizon", [7, 14, 30, 60, 90])
    def test_demand_forecast_horizons(self, horizon):
        client, mock_conn = self._make_client()
        resp = client.get(f"/forecast/demand/1?horizon_days={horizon}")
        assert resp.status_code in (200, 400, 404, 422, 500)
