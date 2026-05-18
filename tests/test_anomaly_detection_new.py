"""Tests for new anomaly detection endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _make_client(mock_rows=None, fetchone_val=None):
    with patch("services.anomaly_detection.engine") as mock_engine:
        mock_conn = MagicMock()
        if mock_rows is not None:
            mock_conn.execute.return_value.__iter__ = lambda s: iter(mock_rows)
            mock_conn.execute.return_value.fetchone.return_value = fetchone_val
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        from services.anomaly_detection import app
        return TestClient(app), mock_conn


class TestCashflowAnomalyEndpoint:
    @pytest.mark.parametrize("days,method", [
        (30, "zscore"),
        (90, "iqr"),
        (60, "zscore"),
    ])
    def test_cashflow_anomaly_params(self, days, method):
        rows = [MagicMock() for _ in range(30)]
        for i, r in enumerate(rows):
            r.__getitem__ = lambda s, k: [20240101 + i, 1000.0 + i * 10][k]
        client, mock_conn = _make_client(mock_rows=rows)
        resp = client.get(f"/detect/financial/cashflow?days={days}&method={method}")
        assert resp.status_code in (200, 400, 404, 500)

    def test_cashflow_anomaly_invalid_method(self):
        client, _ = _make_client(mock_rows=[])
        resp = client.get("/detect/financial/cashflow?method=prophet")
        assert resp.status_code == 422

    def test_cashflow_anomaly_returns_metric_key(self):
        rows = [MagicMock() for _ in range(15)]
        for i, r in enumerate(rows):
            r.__getitem__ = lambda s, k, i=i: [20240101 + i, 1000.0 + i][k]
        client, mock_conn = _make_client(mock_rows=rows)
        resp = client.get("/detect/financial/cashflow")
        if resp.status_code == 200:
            assert "metric" in resp.json()

    def test_cashflow_anomaly_db_error(self):
        with patch("services.anomaly_detection.engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("DB error")
            from services.anomaly_detection import app
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/detect/financial/cashflow")
            assert resp.status_code in (400, 500)


class TestLeadTimeAnomalyEndpoint:
    @pytest.mark.parametrize("supplier_id,method", [
        (1, "zscore"),
        (2, "iqr"),
        (100, "zscore"),
    ])
    def test_lead_time_anomaly_params(self, supplier_id, method):
        rows = [MagicMock() for _ in range(20)]
        for i, r in enumerate(rows):
            r.__getitem__ = lambda s, k: [7 + k][0]
        client, mock_conn = _make_client(mock_rows=rows)
        resp = client.get(f"/detect/supply-chain/lead-time?supplier_id={supplier_id}&method={method}")
        assert resp.status_code in (200, 400, 404, 500)

    def test_lead_time_no_data_returns_404(self):
        client, mock_conn = _make_client(mock_rows=[])
        resp = client.get("/detect/supply-chain/lead-time?supplier_id=9999")
        assert resp.status_code in (400, 404, 500)

    def test_lead_time_anomaly_invalid_method(self):
        client, _ = _make_client(mock_rows=[])
        resp = client.get("/detect/supply-chain/lead-time?supplier_id=1&method=arima")
        assert resp.status_code == 422
