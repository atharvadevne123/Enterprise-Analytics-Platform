"""Tests for centralized service settings."""

from __future__ import annotations

import os
from unittest.mock import patch


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
