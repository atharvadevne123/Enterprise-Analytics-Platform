"""Tests for centralized service settings."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


class TestSettingsDefaults:
    def test_database_url_has_default(self):
        from config.settings import Settings

        assert Settings.database_url is not None
        assert len(Settings.database_url) > 0

    def test_kafka_brokers_is_list(self):
        from config.settings import Settings

        assert isinstance(Settings.kafka_brokers, list)
        assert len(Settings.kafka_brokers) >= 1

    def test_default_ports_are_valid(self):
        from config.settings import Settings

        assert 1 <= Settings.analytics_api_port <= 65535
        assert 1 <= Settings.anomaly_detection_port <= 65535
        assert 1 <= Settings.forecasting_service_port <= 65535

    def test_zscore_threshold_positive(self):
        from config.settings import Settings

        assert Settings.zscore_threshold > 0

    def test_iqr_multiplier_positive(self):
        from config.settings import Settings

        assert Settings.iqr_multiplier > 0

    def test_log_level_valid(self):
        from config.settings import Settings

        assert Settings.log_level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

    def test_api_workers_at_least_one(self):
        from config.settings import Settings

        assert Settings.api_workers >= 1


class TestSettingsEnvironmentOverride:
    def test_sqlite_database_url_override(self):
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///./test.db"}):
            import importlib

            import config.settings as cfg

            importlib.reload(cfg)
            assert "sqlite" in cfg.Settings.database_url

    def test_kafka_brokers_override(self):
        with patch.dict(os.environ, {"KAFKA_BROKERS": "broker1:9092,broker2:9092"}):
            import importlib

            import config.settings as cfg

            importlib.reload(cfg)
            assert len(cfg.Settings.kafka_brokers) == 2

    def test_zscore_threshold_override(self):
        with patch.dict(os.environ, {"ZSCORE_THRESHOLD": "3.0"}):
            import importlib

            import config.settings as cfg

            importlib.reload(cfg)
            assert cfg.Settings.zscore_threshold == 3.0


class TestSettingsMethods:
    def test_is_test_environment_sqlite(self):
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///./test.db"}):
            import importlib

            import config.settings as cfg

            importlib.reload(cfg)
            assert cfg.Settings.is_test_environment() is True

    def test_is_test_environment_postgres(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@host/db"}):
            import importlib

            import config.settings as cfg

            importlib.reload(cfg)
            assert cfg.Settings.is_test_environment() is False

    def test_as_dict_returns_dict(self):
        from config.settings import Settings

        d = Settings.as_dict()
        assert isinstance(d, dict)
        assert "kafka_brokers" in d
        assert "log_level" in d
        assert "is_test" in d

    def test_as_dict_does_not_expose_credentials(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:secret@localhost/db"}):
            import importlib

            import config.settings as cfg

            importlib.reload(cfg)
            d = cfg.Settings.as_dict()
            assert "secret" not in str(d)


# ---------------------------------------------------------------------------
# Additional settings tests
# ---------------------------------------------------------------------------


class TestSettingsThresholdDefaults:
    def test_default_zscore_threshold(self):
        from config.settings import Settings

        assert Settings.zscore_threshold == pytest.approx(2.0)

    def test_default_iqr_multiplier(self):
        from config.settings import Settings

        assert Settings.iqr_multiplier == pytest.approx(1.5)

    def test_default_forecast_horizon(self):
        from config.settings import Settings

        assert Settings.default_forecast_horizon_days == 30

    def test_kafka_brokers_is_list(self):
        from config.settings import Settings

        assert isinstance(Settings.kafka_brokers, list)
        assert len(Settings.kafka_brokers) >= 1

    @pytest.mark.parametrize("env_val,expected", [
        ("2.5", 2.5),
        ("3.0", 3.0),
        ("1.0", 1.0),
    ])
    def test_zscore_threshold_from_env(self, env_val, expected):
        import importlib

        with patch.dict(os.environ, {"ZSCORE_THRESHOLD": env_val}):
            import config.settings as cfg

            importlib.reload(cfg)
            assert cfg.Settings.zscore_threshold == pytest.approx(expected)

    @pytest.mark.parametrize("brokers,expected_count", [
        ("localhost:9092", 1),
        ("broker1:9092,broker2:9092", 2),
        ("b1:9092,b2:9092,b3:9092", 3),
    ])
    def test_kafka_brokers_parsing(self, brokers, expected_count):
        import importlib

        with patch.dict(os.environ, {"KAFKA_BROKERS": brokers}):
            import config.settings as cfg

            importlib.reload(cfg)
            assert len(cfg.Settings.kafka_brokers) == expected_count
