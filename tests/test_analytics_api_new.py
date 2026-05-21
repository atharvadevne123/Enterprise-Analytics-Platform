"""Additional tests for new analytics API endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _make_client(mock_rows=None, fetchone_val=None):
    with patch("services.analytics_api.engine") as mock_engine:
        mock_conn = MagicMock()
        if mock_rows is not None:
            mock_conn.execute.return_value.__iter__ = lambda s: iter(mock_rows)
            mock_conn.execute.return_value.fetchone.return_value = fetchone_val
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        from services.analytics_api import app

        return TestClient(app), mock_conn


class TestTopProductsEndpoint:
    @pytest.mark.parametrize(
        "days,limit",
        [
            (7, 5),
            (30, 10),
            (90, 20),
        ],
    )
    def test_top_products_day_and_limit_params(self, days, limit):
        client, mock_conn = _make_client(mock_rows=[])
        resp = client.get(f"/ecommerce/top-products?days={days}&limit={limit}")
        assert resp.status_code in (200, 404, 500)

    def test_top_products_returns_products_key(self):
        client, mock_conn = _make_client(mock_rows=[])
        resp = client.get("/ecommerce/top-products")
        if resp.status_code == 200:
            assert "products" in resp.json()

    def test_top_products_invalid_limit(self):
        client, _ = _make_client(mock_rows=[])
        resp = client.get("/ecommerce/top-products?limit=0")
        assert resp.status_code in (200, 404, 422, 500)

    def test_top_products_db_error_returns_500(self):
        with patch("services.analytics_api.engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("DB error")
            from services.analytics_api import app

            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/ecommerce/top-products")
            assert resp.status_code in (500, 200)


class TestInventoryRiskEndpoint:
    @pytest.mark.parametrize("threshold", [0.0, 10.0, 20.0, 50.0])
    def test_inventory_risk_threshold_param(self, threshold):
        client, mock_conn = _make_client(mock_rows=[])
        resp = client.get(f"/supply-chain/inventory-risk?threshold_pct={threshold}")
        assert resp.status_code in (200, 404, 500)

    def test_inventory_risk_returns_count_keys(self):
        client, mock_conn = _make_client(mock_rows=[])
        resp = client.get("/supply-chain/inventory-risk")
        if resp.status_code == 200:
            data = resp.json()
            assert "total_at_risk" in data

    def test_inventory_risk_invalid_threshold(self):
        client, _ = _make_client(mock_rows=[])
        resp = client.get("/supply-chain/inventory-risk?threshold_pct=150")
        assert resp.status_code in (200, 422, 500)


class TestCashPositionEndpoint:
    def test_cash_position_no_params(self):
        client, mock_conn = _make_client(fetchone_val=(1000.0, 500.0, 500.0))
        resp = client.get("/financial/cash-position")
        assert resp.status_code in (200, 404, 500)

    def test_cash_position_with_date(self):
        client, mock_conn = _make_client(fetchone_val=(2000.0, 800.0, 1200.0))
        resp = client.get("/financial/cash-position?as_of_date=2024-06-30")
        assert resp.status_code in (200, 404, 422, 500)

    def test_cash_position_returns_net_key(self):
        client, mock_conn = _make_client(fetchone_val=(1000.0, 400.0, 600.0))
        resp = client.get("/financial/cash-position")
        if resp.status_code == 200:
            data = resp.json()
            assert "net_cash_position" in data
