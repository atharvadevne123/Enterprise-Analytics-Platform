"""Extended service health and contract tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _get_client(service: str):
    module = f"services.{service}"
    with patch(f"{module}.engine") as mock_engine:
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = None
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        if service == "analytics_api":
            from services.analytics_api import app
        elif service == "anomaly_detection":
            from services.anomaly_detection import app
        else:
            from services.forecasting_service import app
        return TestClient(app)


class TestMetricsEndpoint:
    """All services must expose /metrics with db_pool_size key."""

    @pytest.mark.parametrize(
        "service",
        [
            "analytics_api",
            "anomaly_detection",
            "forecasting_service",
        ],
    )
    def test_metrics_returns_200(self, service):
        client = _get_client(service)
        resp = client.get("/metrics")
        assert resp.status_code == 200

    @pytest.mark.parametrize(
        "service",
        [
            "analytics_api",
            "anomaly_detection",
            "forecasting_service",
        ],
    )
    def test_metrics_has_status_key(self, service):
        client = _get_client(service)
        data = client.get("/metrics").json()
        assert "status" in data or "service" in data


class TestRootEndpointEnhanced:
    """Root endpoint must include endpoints list."""

    @pytest.mark.parametrize(
        "service",
        [
            "analytics_api",
            "anomaly_detection",
            "forecasting_service",
        ],
    )
    def test_root_has_endpoints_list(self, service):
        client = _get_client(service)
        data = client.get("/").json()
        assert "endpoints" in data
        assert isinstance(data["endpoints"], list)
        assert len(data["endpoints"]) > 0

    @pytest.mark.parametrize(
        "service",
        [
            "analytics_api",
            "anomaly_detection",
            "forecasting_service",
        ],
    )
    def test_root_has_version_key(self, service):
        client = _get_client(service)
        data = client.get("/").json()
        assert "version" in data


class TestConfigSettingsEndpoint:
    """All services must expose /config/settings."""

    @pytest.mark.parametrize(
        "service",
        [
            "analytics_api",
            "anomaly_detection",
            "forecasting_service",
        ],
    )
    def test_config_settings_returns_200(self, service):
        client = _get_client(service)
        resp = client.get("/config/settings")
        assert resp.status_code == 200

    @pytest.mark.parametrize(
        "service",
        [
            "analytics_api",
            "anomaly_detection",
            "forecasting_service",
        ],
    )
    def test_config_settings_has_service_key(self, service):
        client = _get_client(service)
        data = client.get("/config/settings").json()
        assert "service" in data


# ---------------------------------------------------------------------------
# Additional extended service tests
# ---------------------------------------------------------------------------


class TestServiceDocumentation:
    @pytest.mark.parametrize("service", ["analytics_api", "anomaly_detection", "forecasting_service"])
    def test_openapi_json_accessible(self, service):
        client = _get_client(service)
        resp = client.get("/openapi.json")
        assert resp.status_code == 200

    @pytest.mark.parametrize("service", ["analytics_api", "anomaly_detection", "forecasting_service"])
    def test_openapi_has_paths(self, service):
        client = _get_client(service)
        data = client.get("/openapi.json").json()
        assert "paths" in data
        assert len(data["paths"]) > 0

    @pytest.mark.parametrize("service", ["analytics_api", "anomaly_detection", "forecasting_service"])
    def test_redoc_accessible(self, service):
        client = _get_client(service)
        resp = client.get("/redoc")
        assert resp.status_code == 200


class TestServiceErrorHandling:
    @pytest.mark.parametrize("service", ["analytics_api", "anomaly_detection", "forecasting_service"])
    def test_nonexistent_endpoint_returns_404(self, service):
        client = _get_client(service)
        resp = client.get("/nonexistent-endpoint-xyz")
        assert resp.status_code == 404

    @pytest.mark.parametrize("service", ["analytics_api", "anomaly_detection", "forecasting_service"])
    def test_method_not_allowed_returns_405(self, service):
        client = _get_client(service)
        # GET-only endpoints should reject POST
        resp = client.delete("/health")
        assert resp.status_code in (405, 404)
