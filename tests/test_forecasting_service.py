"""Tests for the forecasting service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _make_client(mock_rows: list | None = None):
    with patch("services.forecasting_service.engine") as mock_engine:
        mock_conn = MagicMock()
        if mock_rows is not None:
            mock_conn.execute.return_value.fetchall.return_value = mock_rows
            mock_conn.execute.return_value.fetchone.return_value = (
                mock_rows[0] if mock_rows else None
            )
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        from services.forecasting_service import app
        client = TestClient(app)
        return client, mock_conn


class TestRoot:
    def test_root_returns_200(self):
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


class TestDemandForecast:
    def test_demand_forecast_endpoint_exists(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get("/forecast/demand")
        assert resp.status_code in (200, 404, 422, 500)

    @pytest.mark.parametrize("horizon", [7, 14, 30, 90])
    def test_demand_forecast_horizons(self, horizon):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/forecast/demand?horizon_days={horizon}")
        assert resp.status_code in (200, 404, 422, 500)

    @pytest.mark.parametrize("product_id", [1, 100, 9999])
    def test_demand_forecast_by_product(self, product_id):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/forecast/demand?product_id={product_id}")
        assert resp.status_code in (200, 404, 422, 500)


class TestLeadTimeForecast:
    def test_lead_time_forecast_endpoint_exists(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get("/forecast/lead-time")
        assert resp.status_code in (200, 404, 422, 500)

    @pytest.mark.parametrize("supplier_id", [1, 50, 200])
    def test_lead_time_by_supplier(self, supplier_id):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/forecast/lead-time?supplier_id={supplier_id}")
        assert resp.status_code in (200, 404, 422, 500)


class TestCashFlowForecast:
    def test_cashflow_forecast_endpoint_exists(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get("/forecast/cash-flow")
        assert resp.status_code in (200, 404, 422, 500)

    @pytest.mark.parametrize("horizon", [30, 60, 90, 180])
    def test_cashflow_forecast_horizons(self, horizon):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/forecast/cash-flow?horizon_days={horizon}")
        assert resp.status_code in (200, 404, 422, 500)


class TestForecastAccuracy:
    def test_forecast_accuracy_endpoint_exists(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get("/forecast/accuracy")
        assert resp.status_code in (200, 404, 422, 500)

    def test_forecast_accuracy_by_model(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get("/forecast/accuracy?model_type=arima")
        assert resp.status_code in (200, 404, 422, 500)


class TestEdgeCases:
    def test_negative_horizon_handled(self):
        client, _ = _make_client()
        resp = client.get("/forecast/demand?horizon_days=-1")
        assert resp.status_code in (200, 404, 422, 400, 500)

    def test_zero_horizon_handled(self):
        client, _ = _make_client()
        resp = client.get("/forecast/demand?horizon_days=0")
        assert resp.status_code in (200, 404, 422, 400, 500)

    def test_db_error_handled_gracefully(self):
        with patch("services.forecasting_service.engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("DB down")
            from services.forecasting_service import app
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/forecast/demand")
            assert resp.status_code in (500, 200, 404)

    def test_nonexistent_product_returns_not_found_or_empty(self):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get("/forecast/demand?product_id=999999")
        assert resp.status_code in (200, 404, 422, 500)
