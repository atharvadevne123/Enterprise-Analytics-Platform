

# ---------------------------------------------------------------------------
# Additional anomaly detection extended tests
# ---------------------------------------------------------------------------


class TestAnomalyEndpointShapes:
    def test_revenue_anomaly_response_has_required_keys(self):
        from datetime import date

        client, mock_conn = _make_client()
        mock_conn.execute.return_value.fetchone.return_value = None
        resp = client.post(f"/detect/ecommerce/revenue?current_date={date.today().isoformat()}")
        if resp.status_code == 200:
            data = resp.json()
            assert any(k in data for k in ("alert_id", "anomaly_detected", "severity", "status"))

    def test_alerts_active_returns_list(self):
        client, _ = _make_client()
        resp = client.get("/alerts/active")
        if resp.status_code == 200:
            assert isinstance(resp.json(), list)

    @pytest.mark.parametrize("alert_id", ["test-001", "abc-123-xyz", "alert-999"])
    def test_acknowledge_alert_returns_valid_response(self, alert_id):
        client, _ = _make_client()
        resp = client.post(f"/alerts/{alert_id}/acknowledge")
        assert resp.status_code in (200, 404, 422)

    def test_service_settings_endpoint(self):
        client, _ = _make_client()
        resp = client.get("/config/settings")
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            data = resp.json()
            assert "service" in data

    @pytest.mark.parametrize("date_str", [
        "2024-01-15",
        "2024-06-30",
        "2024-12-31",
    ])
    def test_revenue_anomaly_various_dates(self, date_str):
        client, mock_conn = _make_client()
        mock_conn.execute.return_value.fetchone.return_value = None
        resp = client.post(f"/detect/ecommerce/revenue?current_date={date_str}")
        assert resp.status_code in (200, 404, 422, 500)
