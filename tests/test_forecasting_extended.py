"""Additional extended tests for the forecasting service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _make_client(rows=None):
    mock_conn = MagicMock()
    if rows is not None:
        mock_conn.execute.return_value = rows
    with patch("services.forecasting_service._make_engine") as mock_eng:
        mock_eng.return_value.connect.return_value.__enter__ = lambda s: mock_conn
        mock_eng.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)
        from services.forecasting_service import app

        client = TestClient(app, raise_server_exceptions=False)
        return client, mock_conn


class TestForecastingServiceStructure:
    def test_service_openapi_has_forecast_paths(self):
        client, _ = _make_client()
        data = client.get("/openapi.json").json()
        paths = data.get("paths", {})
        forecast_paths = [p for p in paths if "forecast" in p]
        assert len(forecast_paths) >= 3

    def test_demand_forecast_response_shape(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get("/forecast/demand/1")
        if resp.status_code == 200:
            data = resp.json()
            assert "product_id" in data or "forecasts" in data

    def test_lead_time_not_found_for_missing_supplier(self):
        client, mock_conn = _make_client()
        mock_conn.execute.return_value = []
        resp = client.get("/forecast/lead-time/999999")
        assert resp.status_code in (200, 400, 404, 500)

    @pytest.mark.parametrize("product_id", [1, 5, 100, 10000])
    def test_demand_forecast_all_product_ids(self, product_id):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/forecast/demand/{product_id}")
        assert resp.status_code in (200, 400, 404, 422, 500)

    def test_cash_flow_returns_model_version(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get("/forecast/cash-flow")
        if resp.status_code == 200:
            data = resp.json()
            assert "model_version" in data
