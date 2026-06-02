"""Tests for Settings.validate() configuration validation method."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


class TestSettingsValidateDefaults:
    """Default settings should pass validation with no errors."""

    def test_valid_defaults_return_empty_list(self):
        from config.settings import Settings
        errors = Settings.validate()
        assert errors == []

    def test_returns_list_type(self):
        from config.settings import Settings
        assert isinstance(Settings.validate(), list)


class TestSettingsValidateThresholds:
    """Out-of-range thresholds should produce descriptive error messages."""

    def test_negative_zscore_threshold_is_invalid(self):
        from importlib import reload
        with patch.dict(os.environ, {"ZSCORE_THRESHOLD": "-1.0"}):
            import config.settings as m
            reload(m)
            errors = m.Settings.validate()
            assert any("ZSCORE_THRESHOLD" in e for e in errors)

    def test_zero_iqr_multiplier_is_invalid(self):
        from importlib import reload
        with patch.dict(os.environ, {"IQR_MULTIPLIER": "0"}):
            import config.settings as m
            reload(m)
            errors = m.Settings.validate()
            assert any("IQR_MULTIPLIER" in e for e in errors)

    def test_zero_history_days_is_invalid(self):
        from importlib import reload
        with patch.dict(os.environ, {"MAX_HISTORY_DAYS": "0"}):
            import config.settings as m
            reload(m)
            errors = m.Settings.validate()
            assert any("MAX_HISTORY_DAYS" in e for e in errors)

    def test_zero_min_data_points_is_invalid(self):
        from importlib import reload
        with patch.dict(os.environ, {"MIN_ANOMALY_DATA_POINTS": "0"}):
            import config.settings as m
            reload(m)
            errors = m.Settings.validate()
            assert any("MIN_ANOMALY_DATA_POINTS" in e for e in errors)


class TestSettingsValidatePorts:
    """Port numbers outside 1-65535 should be flagged."""

    @pytest.mark.parametrize("env_var,expected_fragment", [
        ("ANALYTICS_API_PORT", "ANALYTICS_API_PORT"),
        ("ANOMALY_DETECTION_PORT", "ANOMALY_DETECTION_PORT"),
        ("FORECASTING_SERVICE_PORT", "FORECASTING_SERVICE_PORT"),
    ])
    def test_port_zero_is_invalid(self, env_var, expected_fragment):
        from importlib import reload
        with patch.dict(os.environ, {env_var: "0"}):
            import config.settings as m
            reload(m)
            errors = m.Settings.validate()
            assert any(expected_fragment in e for e in errors)

    @pytest.mark.parametrize("env_var", [
        "ANALYTICS_API_PORT",
        "ANOMALY_DETECTION_PORT",
        "FORECASTING_SERVICE_PORT",
    ])
    def test_valid_port_no_error(self, env_var):
        from importlib import reload
        with patch.dict(os.environ, {env_var: "8080"}):
            import config.settings as m
            reload(m)
            errors = m.Settings.validate()
            port_errors = [e for e in errors if env_var in e]
            assert port_errors == []


class TestSettingsValidateMultipleErrors:
    """Multiple bad values should accumulate multiple error strings."""

    def test_multiple_invalid_settings_produce_multiple_errors(self):
        from importlib import reload
        with patch.dict(os.environ, {"ZSCORE_THRESHOLD": "-1", "IQR_MULTIPLIER": "0"}):
            import config.settings as m
            reload(m)
            errors = m.Settings.validate()
            assert len(errors) >= 2
