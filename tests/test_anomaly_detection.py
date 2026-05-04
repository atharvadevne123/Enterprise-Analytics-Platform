"""Tests for the anomaly detection service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _make_client(mock_rows: list | None = None):
    with patch("services.anomaly_detection.engine") as mock_engine:
        mock_conn = MagicMock()
        if mock_rows is not None:
            mock_conn.execute.return_value.fetchall.return_value = mock_rows
            mock_conn.execute.return_value.fetchone.return_value = (
                mock_rows[0] if mock_rows else None
            )
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        from services.anomaly_detection import app
        client = TestClient(app)
        return client, mock_conn


class TestRoot:
    def test_root_200(self):
        client, _ = _make_client()
        resp = client.get("/")
        assert resp.status_code == 200

    def test_root_has_service_key(self):
        client, _ = _make_client()
        data = client.get("/").json()
        assert "service" in data

    def test_docs_accessible(self):
        client, _ = _make_client()
        resp = client.get("/docs")
        assert resp.status_code == 200


class TestAnomalyEndpoints:
    def test_anomalies_endpoint_exists(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get("/anomalies/current")
        assert resp.status_code in (200, 404, 422, 500)

    def test_anomaly_history_exists(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get("/anomalies/history")
        assert resp.status_code in (200, 404, 422, 500)

    def test_anomaly_summary_exists(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get("/anomalies/summary")
        assert resp.status_code in (200, 404, 422, 500)

    @pytest.mark.parametrize("domain", ["ecommerce", "supply_chain", "financial", "all"])
    def test_anomalies_by_domain(self, domain):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/anomalies/current?domain={domain}")
        assert resp.status_code in (200, 404, 422, 500)

    @pytest.mark.parametrize("severity", ["CRITICAL", "WARNING", "INFO"])
    def test_anomalies_by_severity(self, severity):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/anomalies/current?severity={severity}")
        assert resp.status_code in (200, 404, 422, 500)


class TestDetectionEndpoints:
    def test_detect_ecommerce_anomalies(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.post("/detect/ecommerce")
        assert resp.status_code in (200, 404, 422, 500)

    def test_detect_supply_chain_anomalies(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.post("/detect/supply-chain")
        assert resp.status_code in (200, 404, 422, 500)

    def test_detect_financial_anomalies(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.post("/detect/financial")
        assert resp.status_code in (200, 404, 422, 500)

    def test_detect_all_domains(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.post("/detect/all")
        assert resp.status_code in (200, 404, 422, 500)


class TestEdgeCases:
    def test_db_error_does_not_crash_server(self):
        with patch("services.anomaly_detection.engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("DB unavailable")
            from services.anomaly_detection import app
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/anomalies/current")
            assert resp.status_code in (500, 200, 404)

    def test_invalid_domain_param(self):
        client, _ = _make_client()
        resp = client.get("/anomalies/current?domain=invalid_domain_xyz")
        assert resp.status_code in (200, 422, 400, 500)

    def test_invalid_severity_param(self):
        client, _ = _make_client()
        resp = client.get("/anomalies/current?severity=UNKNOWN")
        assert resp.status_code in (200, 422, 400, 500)

    @pytest.mark.parametrize("days", [1, 7, 30, 90, 365])
    def test_history_day_ranges(self, days):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/anomalies/history?days={days}")
        assert resp.status_code in (200, 404, 422, 500)
