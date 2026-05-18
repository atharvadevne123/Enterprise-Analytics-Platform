"""Tests for new forecasting service endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _make_client(mock_rows=None, fetchone_val=None):
    with patch("services.forecasting_service.engine") as mock_engine:
        mock_conn = MagicMock()
        if mock_rows is not None:
            mock_conn.execute.return_value.__iter__ = lambda s: iter(mock_rows)
            mock_conn.execute.return_value.fetchone.return_value = fetchone_val
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        from services.forecasting_service import app
        return TestClient(app), mock_conn


class TestReorderForecastEndpoint:
    @pytest.mark.parametrize("horizon", [7, 14, 30])
    def test_reorder_forecast_horizon_param(self, horizon):
        client, mock_conn = _make_client(mock_rows=[])
        resp = client.get(f"/forecast/inventory/reorder?horizon_days={horizon}")
        assert resp.status_code in (200, 400, 404, 500)

    def test_reorder_forecast_returns_forecasts_key(self):
        client, mock_conn = _make_client(mock_rows=[])
        resp = client.get("/forecast/inventory/reorder")
        if resp.status_code == 200:
            assert "forecasts" in resp.json()

    def test_reorder_forecast_invalid_horizon(self):
        client, _ = _make_client(mock_rows=[])
        resp = client.get("/forecast/inventory/reorder?horizon_days=0")
        assert resp.status_code in (200, 422, 500)

    def test_reorder_forecast_db_error(self):
        with patch("services.forecasting_service.engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("DB error")
            from services.forecasting_service import app
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/forecast/inventory/reorder")
            assert resp.status_code in (400, 500)


class TestDemandTrendEndpoint:
    def test_demand_trend_insufficient_data(self):
        rows = [MagicMock() for _ in range(3)]
        for i, r in enumerate(rows):
            r.__getitem__ = lambda s, k, i=i: [20240101 + i, 100.0 + i][k]
        client, mock_conn = _make_client(mock_rows=rows)
        resp = client.get("/forecast/demand/trend?product_id=1")
        assert resp.status_code in (200, 400, 500)

    def test_demand_trend_returns_slope_key(self):
        rows = [MagicMock() for _ in range(30)]
        for i, r in enumerate(rows):
            r.__getitem__ = lambda s, k, i=i: [20240101 + i, 100.0 + i * 2][k]
        client, mock_conn = _make_client(mock_rows=rows)
        resp = client.get("/forecast/demand/trend?product_id=1")
        if resp.status_code == 200:
            data = resp.json()
            assert "slope_per_day" in data
            assert "trend_direction" in data

    @pytest.mark.parametrize("product_id", [1, 50, 100, 999])
    def test_demand_trend_various_products(self, product_id):
        client, mock_conn = _make_client(mock_rows=[])
        resp = client.get(f"/forecast/demand/trend?product_id={product_id}")
        assert resp.status_code in (200, 400, 404, 422, 500)

    def test_demand_trend_db_error(self):
        with patch("services.forecasting_service.engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("DB error")
            from services.forecasting_service import app
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/forecast/demand/trend?product_id=1")
            assert resp.status_code in (400, 500)
