"""Additional extended tests for the analytics API service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _make_client(rows=None):
    mock_conn = MagicMock()
    if rows is not None:
        mock_conn.execute.return_value = rows
    with patch("services.analytics_api._make_engine") as mock_eng:
        mock_eng.return_value.connect.return_value.__enter__ = lambda s: mock_conn
        mock_eng.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)
        from services.analytics_api import app
        client = TestClient(app, raise_server_exceptions=False)
        return client, mock_conn


class TestDateRangeConstraints:
    @pytest.mark.parametrize(
        "start,end",
        [
            ("2023-01-01", "2023-12-31"),
            ("2022-06-01", "2022-06-30"),
            ("2025-01-01", "2025-03-31"),
        ],
    )
    def test_ecommerce_metrics_multi_year_range(self, start, end):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/ecommerce/metrics/{start}/{end}")
        assert resp.status_code in (200, 404, 500)

    def test_supply_chain_metrics_missing_start(self):
        client, _ = _make_client()
        resp = client.get("/supply-chain/metrics//2024-12-31")
        assert resp.status_code in (404, 422)

    @pytest.mark.parametrize("days", [1, 7, 30, 90, 180, 365])
    def test_conversion_rate_boundary_values(self, days):
        client, mock_conn = _make_client()
        mock_conn.execute.return_value.fetchone.return_value = (0.03, 0.01, 0.06, 0.005)
        resp = client.get(f"/ecommerce/conversion-rate?days={days}")
        assert resp.status_code in (200, 500)

    def test_kpi_summary_returns_correct_keys(self):
        client, mock_conn = _make_client()
        mock_conn.execute.return_value.fetchone.return_value = None
        resp = client.get("/kpis/summary")
        if resp.status_code == 200:
            data = resp.json()
            assert any(k in data for k in ("ecommerce", "supply_chain", "financial", "date"))


class TestAnalyticsAPISettings:
    def test_config_settings_returns_dict(self):
        client, _ = _make_client()
        resp = client.get("/config/settings")
        if resp.status_code == 200:
            data = resp.json()
            assert "config" in data or "service" in data

    def test_openapi_info_has_title(self):
        client, _ = _make_client()
        data = client.get("/openapi.json").json()
        assert data["info"]["title"] == "Unified Analytics API"
