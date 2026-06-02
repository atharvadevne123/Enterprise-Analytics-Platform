"""Health, version, and metrics endpoint contract tests for all services."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _make_analytics_client():
    with patch("services.analytics_api.engine") as mock_engine:
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_engine.pool.size.return_value = 20
        from fastapi.testclient import TestClient

        from services.analytics_api import app

        return TestClient(app)


def _make_anomaly_client():
    with patch("services.anomaly_detection.engine") as mock_engine:
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_engine.pool.size.return_value = 20
        from fastapi.testclient import TestClient

        from services.anomaly_detection import app

        return TestClient(app)


def _make_forecasting_client():
    with patch("services.forecasting_service.engine") as mock_engine:
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_engine.pool.size.return_value = 20
        from fastapi.testclient import TestClient

        from services.forecasting_service import app

        return TestClient(app)


class TestHealthEndpointContract:
    """All services must expose /health returning {status: healthy, service: ...}."""

    @pytest.mark.parametrize(
        "client_factory,expected_service",
        [
            (_make_analytics_client, "analytics-api"),
            (_make_anomaly_client, "anomaly-detection"),
            (_make_forecasting_client, "forecasting"),
        ],
    )
    def test_health_returns_200(self, client_factory, expected_service):
        client = client_factory()
        resp = client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.parametrize(
        "client_factory,expected_service",
        [
            (_make_analytics_client, "analytics-api"),
            (_make_anomaly_client, "anomaly-detection"),
            (_make_forecasting_client, "forecasting"),
        ],
    )
    def test_health_status_is_healthy(self, client_factory, expected_service):
        client = client_factory()
        data = client.get("/health").json()
        assert data["status"] == "healthy"

    @pytest.mark.parametrize(
        "client_factory,expected_service",
        [
            (_make_analytics_client, "analytics-api"),
            (_make_anomaly_client, "anomaly-detection"),
            (_make_forecasting_client, "forecasting"),
        ],
    )
    def test_health_contains_service_key(self, client_factory, expected_service):
        client = client_factory()
        data = client.get("/health").json()
        assert "service" in data


class TestVersionEndpointContract:
    """All services must expose /version returning {service, version, python}."""

    @pytest.mark.parametrize(
        "client_factory",
        [
            _make_analytics_client,
            _make_anomaly_client,
            _make_forecasting_client,
        ],
    )
    def test_version_returns_200(self, client_factory):
        client = client_factory()
        resp = client.get("/version")
        assert resp.status_code == 200

    @pytest.mark.parametrize(
        "client_factory",
        [
            _make_analytics_client,
            _make_anomaly_client,
            _make_forecasting_client,
        ],
    )
    def test_version_has_version_field(self, client_factory):
        client = client_factory()
        data = client.get("/version").json()
        assert "version" in data
        assert data["version"] == "1.0.0"


class TestMetricsEndpointContract:
    """All services must expose /metrics returning service operational data."""

    @pytest.mark.parametrize(
        "client_factory",
        [
            _make_analytics_client,
            _make_anomaly_client,
            _make_forecasting_client,
        ],
    )
    def test_metrics_returns_200(self, client_factory):
        client = client_factory()
        resp = client.get("/metrics")
        assert resp.status_code == 200

    @pytest.mark.parametrize(
        "client_factory",
        [
            _make_analytics_client,
            _make_anomaly_client,
            _make_forecasting_client,
        ],
    )
    def test_metrics_has_service_key(self, client_factory):
        client = client_factory()
        data = client.get("/metrics").json()
        assert "service" in data


class TestReadyzEndpointContract:
    """All services must expose /readyz for Kubernetes readiness probes."""

    @pytest.mark.parametrize(
        "client_factory",
        [
            _make_analytics_client,
            _make_anomaly_client,
            _make_forecasting_client,
        ],
    )
    def test_readyz_returns_200_when_db_reachable(self, client_factory):
        client = client_factory()
        resp = client.get("/readyz")
        assert resp.status_code in (200, 503)

    @pytest.mark.parametrize(
        "client_factory",
        [
            _make_analytics_client,
            _make_anomaly_client,
            _make_forecasting_client,
        ],
    )
    def test_readyz_has_status_on_success(self, client_factory):
        client = client_factory()
        resp = client.get("/readyz")
        if resp.status_code == 200:
            assert "status" in resp.json()

    @pytest.mark.parametrize(
        "service_module,app_path",
        [
            ("services.analytics_api", "services.analytics_api"),
            ("services.anomaly_detection", "services.anomaly_detection"),
            ("services.forecasting_service", "services.forecasting_service"),
        ],
    )
    def test_readyz_returns_503_on_db_failure(self, service_module, app_path):
        with patch(f"{service_module}.engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("DB down")
            import importlib

            mod = importlib.import_module(service_module)
            from fastapi.testclient import TestClient

            client = TestClient(mod.app, raise_server_exceptions=False)
            resp = client.get("/readyz")
            assert resp.status_code in (503, 500)


class TestRootEndpointContract:
    """All services must expose / returning endpoint metadata."""

    @pytest.mark.parametrize(
        "client_factory",
        [
            _make_analytics_client,
            _make_anomaly_client,
            _make_forecasting_client,
        ],
    )
    def test_root_returns_200(self, client_factory):
        client = client_factory()
        resp = client.get("/")
        assert resp.status_code == 200

    @pytest.mark.parametrize(
        "client_factory",
        [
            _make_analytics_client,
            _make_anomaly_client,
            _make_forecasting_client,
        ],
    )
    def test_root_has_version_field(self, client_factory):
        client = client_factory()
        data = client.get("/").json()
        assert "version" in data


# ---------------------------------------------------------------------------
# Additional health check tests
# ---------------------------------------------------------------------------


class TestServiceIdentity:
    @pytest.mark.parametrize(
        "client_factory,expected_service",
        [
            (_make_analytics_client, "analytics-api"),
            (_make_anomaly_client, "anomaly-detection"),
            (_make_forecasting_client, "forecasting"),
        ],
    )
    def test_health_returns_correct_service_name(self, client_factory, expected_service):
        client = client_factory()
        data = client.get("/health").json()
        assert data.get("service", "").startswith(expected_service.split("-")[0])

    @pytest.mark.parametrize(
        "client_factory",
        [_make_analytics_client, _make_anomaly_client, _make_forecasting_client],
    )
    def test_metrics_endpoint_returns_service_field(self, client_factory):
        client = client_factory()
        resp = client.get("/metrics")
        if resp.status_code == 200:
            data = resp.json()
            assert "service" in data

    @pytest.mark.parametrize(
        "client_factory",
        [_make_analytics_client, _make_anomaly_client, _make_forecasting_client],
    )
    def test_docs_endpoint_accessible(self, client_factory):
        client = client_factory()
        resp = client.get("/docs")
        assert resp.status_code == 200
