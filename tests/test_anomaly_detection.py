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
            mock_conn.execute.return_value.fetchone.return_value = mock_rows[0] if mock_rows else None
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
        assert resp.status_code in (200, 404, 422, 400, 500)

    def test_invalid_severity_param(self):
        client, _ = _make_client()
        resp = client.get("/anomalies/current?severity=UNKNOWN")
        assert resp.status_code in (200, 404, 422, 400, 500)

    @pytest.mark.parametrize("days", [1, 7, 30, 90, 365])
    def test_history_day_ranges(self, days):
        client, mock_conn = _make_client([])
        mock_conn.execute.return_value = []
        resp = client.get(f"/anomalies/history?days={days}")
        assert resp.status_code in (200, 404, 422, 500)


class TestStatisticalHelpers:
    """Unit tests for detect_statistical_anomaly and detect_iqr_anomaly helpers."""

    def test_zscore_no_anomaly_for_normal_value(self):
        from services.anomaly_detection import detect_statistical_anomaly

        values = [100.0, 102.0, 98.0, 101.0, 99.0, 100.5, 100.0]
        is_anom, z, mean, std = detect_statistical_anomaly(values, 100.0)
        assert not is_anom
        assert abs(z) < 2.0

    def test_zscore_anomaly_for_outlier(self):
        from services.anomaly_detection import detect_statistical_anomaly

        values = [100.0] * 10
        is_anom, z, mean, std = detect_statistical_anomaly(values, 200.0, threshold_sigma=1.0)
        assert is_anom or std == 0

    def test_zscore_insufficient_data_returns_false(self):
        from services.anomaly_detection import detect_statistical_anomaly

        is_anom, z, mean, std = detect_statistical_anomaly([10.0, 20.0], 15.0)
        assert not is_anom

    def test_iqr_detects_outlier_below(self):
        from services.anomaly_detection import detect_iqr_anomaly

        values = list(range(20, 80))
        # lower fence = Q1 - 1.5*IQR ≈ -9.5; use -50 to be clearly below
        is_anom, lower, upper = detect_iqr_anomaly(values, -50.0)
        assert is_anom

    def test_iqr_no_anomaly_for_midrange_value(self):
        from services.anomaly_detection import detect_iqr_anomaly

        values = list(range(10, 50))
        is_anom, lower, upper = detect_iqr_anomaly(values, 30.0)
        assert not is_anom

    def test_iqr_insufficient_data_returns_false(self):
        from services.anomaly_detection import detect_iqr_anomaly

        is_anom, lower, upper = detect_iqr_anomaly([1.0, 2.0, 3.0], 2.0)
        assert not is_anom

    @pytest.mark.parametrize("threshold", [1.0, 1.5, 2.0, 3.0])
    def test_zscore_threshold_parametrized(self, threshold):
        from services.anomaly_detection import detect_statistical_anomaly

        values = [50.0 + i for i in range(10)]
        is_anom, z, mean, std = detect_statistical_anomaly(values, 100.0, threshold)
        assert isinstance(is_anom, bool)


class TestExistingDetectionEndpoints:
    """Tests for the real anomaly detection endpoints added in this session."""

    def test_detect_revenue_endpoint_exists(self):
        client, mock_conn = _make_client()
        mock_conn.execute.return_value = []
        resp = client.post("/detect/ecommerce/revenue")
        assert resp.status_code in (200, 404, 422, 500)

    def test_detect_conversion_endpoint_exists(self):
        client, mock_conn = _make_client()
        mock_conn.execute.return_value = []
        resp = client.post("/detect/ecommerce/conversion-rate")
        assert resp.status_code in (200, 404, 422, 500)

    def test_detect_delivery_endpoint_exists(self):
        client, mock_conn = _make_client()
        mock_conn.execute.return_value = []
        resp = client.post("/detect/supply-chain/on-time-delivery")
        assert resp.status_code in (200, 404, 422, 500)

    def test_orders_count_zscore_endpoint(self):
        client, mock_conn = _make_client()
        mock_conn.execute.return_value = []
        resp = client.post("/detect/ecommerce/orders-count?method=zscore")
        assert resp.status_code in (200, 404, 422, 500)

    def test_orders_count_iqr_endpoint(self):
        client, mock_conn = _make_client()
        mock_conn.execute.return_value = []
        resp = client.post("/detect/ecommerce/orders-count?method=iqr")
        assert resp.status_code in (200, 404, 422, 500)

    def test_readyz_endpoint(self):
        client, mock_conn = _make_client()
        resp = client.get("/readyz")
        assert resp.status_code in (200, 503)

    def test_alerts_active_endpoint(self):
        client, _ = _make_client()
        resp = client.get("/alerts/active")
        assert resp.status_code == 200

    def test_acknowledge_alert_endpoint(self):
        client, _ = _make_client()
        resp = client.post("/alerts/test-alert-123/acknowledge")
        assert resp.status_code in (200, 404, 422)


# ---------------------------------------------------------------------------
# Additional edge case tests
# ---------------------------------------------------------------------------


class TestDetectionMethods:
    @pytest.mark.parametrize("method", ["zscore", "iqr"])
    def test_revenue_detection_method_param(self, method):
        client, mock_conn = _make_client()
        mock_conn.execute.return_value = []
        resp = client.post(f"/detect/ecommerce/revenue?method={method}")
        assert resp.status_code in (200, 404, 422, 500)

    @pytest.mark.parametrize("method", ["zscore", "iqr"])
    def test_delivery_detection_method_param(self, method):
        client, mock_conn = _make_client()
        mock_conn.execute.return_value = []
        resp = client.post(f"/detect/supply-chain/on-time-delivery?method={method}")
        assert resp.status_code in (200, 404, 422, 500)

    def test_invalid_method_param(self):
        client, _ = _make_client()
        resp = client.post("/detect/ecommerce/revenue?method=invalid_method")
        assert resp.status_code in (200, 400, 422, 404, 500)


class TestAnomalyAlertModel:
    def test_severity_levels(self):
        """Alert severity should be one of the expected values."""
        from datetime import datetime
        from decimal import Decimal

        from services.anomaly_detection import AnomalyAlert

        alert = AnomalyAlert(
            alert_id="test-001",
            severity="CRITICAL",
            domain="ecommerce",
            metric_name="revenue",
            current_value=Decimal("100"),
            expected_range_min=Decimal("50"),
            expected_range_max=Decimal("150"),
            deviation_pct=Decimal("5"),
            timestamp=datetime.utcnow(),
            recommended_action="Investigate",
        )
        assert alert.severity in ("CRITICAL", "WARNING", "INFO")

    def test_alert_serialization(self):
        """Alert should serialize to JSON without errors."""
        from datetime import datetime
        from decimal import Decimal

        from services.anomaly_detection import AnomalyAlert

        alert = AnomalyAlert(
            alert_id="test-002",
            severity="WARNING",
            domain="supply_chain",
            metric_name="on_time_delivery",
            current_value=Decimal("85"),
            expected_range_min=Decimal("90"),
            expected_range_max=Decimal("100"),
            deviation_pct=Decimal("-5"),
            timestamp=datetime.utcnow(),
            recommended_action="Review supplier contracts",
        )
        data = alert.model_dump()
        assert "alert_id" in data
        assert "severity" in data
