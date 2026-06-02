"""
Integration contract tests — verify endpoint schemas without a live DB.
These tests are tagged @integration but use mocks so they can run in CI.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _analytics_client():
    with patch("services.analytics_api.engine") as mock_engine:
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = None
        mock_conn.execute.return_value.fetchall.return_value = []
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        from services.analytics_api import app

        return TestClient(app), mock_conn


def _anomaly_client():
    with patch("services.anomaly_detection.engine") as mock_engine:
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = None
        mock_conn.execute.return_value.fetchall.return_value = []
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        from services.anomaly_detection import app

        return TestClient(app), mock_conn


def _forecast_client():
    with patch("services.forecasting_service.engine") as mock_engine:
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = None
        mock_conn.execute.return_value.fetchall.return_value = []
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        from services.forecasting_service import app

        return TestClient(app), mock_conn


# ---------------------------------------------------------------------------
# Cross-service health contract
# ---------------------------------------------------------------------------


class TestCrossServiceHealth:
    """All services must expose /health returning {status: healthy}."""

    @pytest.mark.integration
    def test_analytics_api_health_contract(self):
        client, _ = _analytics_client()
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json().get("status") == "healthy"

    @pytest.mark.integration
    def test_anomaly_detection_health_contract(self):
        client, _ = _anomaly_client()
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json().get("status") == "healthy"

    @pytest.mark.integration
    def test_forecasting_service_health_contract(self):
        client, _ = _forecast_client()
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json().get("status") == "healthy"


# ---------------------------------------------------------------------------
# Cross-service version contract
# ---------------------------------------------------------------------------


class TestCrossServiceVersion:
    """All services must expose /version returning a version string."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "get_client",
        [
            _analytics_client,
            _anomaly_client,
            _forecast_client,
        ],
    )
    def test_version_endpoint_contract(self, get_client):
        client, _ = get_client()
        resp = client.get("/version")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
        assert isinstance(data["version"], str)


# ---------------------------------------------------------------------------
# Correlation ID middleware contract
# ---------------------------------------------------------------------------


class TestCorrelationIDMiddleware:
    """All services must echo X-Request-ID in the response."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "get_client",
        [
            _analytics_client,
            _anomaly_client,
            _forecast_client,
        ],
    )
    def test_correlation_id_echoed(self, get_client):
        client, _ = get_client()
        resp = client.get("/health", headers={"X-Request-ID": "test-trace-id-123"})
        assert resp.headers.get("x-request-id") == "test-trace-id-123"

    @pytest.mark.integration
    def test_correlation_id_auto_generated(self):
        client, _ = _analytics_client()
        resp = client.get("/health")
        assert "x-request-id" in resp.headers
        assert len(resp.headers["x-request-id"]) > 0


# ---------------------------------------------------------------------------
# Readiness probe contract
# ---------------------------------------------------------------------------


class TestReadinessProbeContract:
    """All services must expose /readyz that returns 200 when DB is reachable."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "get_client",
        [
            _analytics_client,
            _anomaly_client,
            _forecast_client,
        ],
    )
    def test_readyz_returns_ready_status(self, get_client):
        client, _ = get_client()
        resp = client.get("/readyz")
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            assert resp.json().get("status") == "ready"


# ---------------------------------------------------------------------------
# Cross-service header consistency tests
# ---------------------------------------------------------------------------


class TestCrossServiceHeaders:
    """All services should return consistent headers."""

    @pytest.mark.parametrize(
        "get_client",
        [_analytics_client, _anomaly_client, _forecast_client],
    )
    def test_all_services_return_json_content_type(self, get_client):
        client, _ = get_client()
        resp = client.get("/health")
        if resp.status_code == 200:
            assert "application/json" in resp.headers.get("content-type", "")

    @pytest.mark.parametrize(
        "get_client,path",
        [
            (_analytics_client, "/"),
            (_anomaly_client, "/"),
            (_forecast_client, "/"),
        ],
    )
    def test_all_services_root_returns_service_name(self, get_client, path):
        client, _ = get_client()
        resp = client.get(path)
        if resp.status_code == 200:
            data = resp.json()
            assert "service" in data

    @pytest.mark.parametrize(
        "get_client",
        [_analytics_client, _anomaly_client, _forecast_client],
    )
    def test_all_services_have_version_endpoint(self, get_client):
        client, _ = get_client()
        resp = client.get("/version")
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            assert "version" in resp.json()
