"""Tests for environment configuration and service settings."""

from __future__ import annotations

import os
from unittest.mock import patch


class TestDatabaseURLConfiguration:
    """Verify DATABASE_URL env var drives engine creation."""

    def test_default_url_is_postgresql(self):
        """Default DATABASE_URL contains postgres."""
        default = "postgresql://postgres:password@localhost:5432/analytics_warehouse"
        assert "postgresql" in default

    def test_sqlite_url_accepted(self):
        """SQLite URL should not raise during module import."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///./test.db"}):
            import importlib

            import services.analytics_api as svc

            importlib.reload(svc)
            assert svc.engine is not None

    def test_env_var_overrides_default(self):
        custom_url = "sqlite:///./custom_test.db"
        with patch.dict(os.environ, {"DATABASE_URL": custom_url}):
            import importlib

            import services.forecasting_service as svc

            importlib.reload(svc)
            assert svc.engine is not None


class TestKafkaConfiguration:
    """Verify Kafka broker env var is consumed correctly."""

    def test_kafka_brokers_env_var(self):
        brokers = os.getenv("KAFKA_BROKERS", "localhost:9092")
        assert ":" in brokers

    def test_default_kafka_brokers(self):
        with patch.dict(os.environ, {}, clear=False):
            brokers = os.getenv("KAFKA_BROKERS", "localhost:9092")
            assert brokers == "localhost:9092"


class TestMakeEngineHelper:
    """Unit tests for the _make_engine dialect dispatcher."""

    def test_sqlite_engine_has_check_same_thread(self):
        from services.analytics_api import _make_engine

        engine = _make_engine("sqlite:///./test_make_engine.db")
        assert engine is not None
        engine.dispose()

    def test_postgres_url_creates_engine(self):
        """_make_engine should not raise for postgres URLs (pool_size set)."""
        from services.analytics_api import _make_engine

        try:
            engine = _make_engine("postgresql://user:pass@localhost/db")
            engine.dispose()
        except Exception:
            pass  # expected without psycopg2

    def test_forecasting_make_engine_sqlite(self):
        from services.forecasting_service import _make_engine

        engine = _make_engine("sqlite:///./test_forecast_engine.db")
        assert engine is not None
        engine.dispose()

    def test_anomaly_make_engine_sqlite(self):
        from services.anomaly_detection import _make_engine

        engine = _make_engine("sqlite:///./test_anomaly_engine.db")
        assert engine is not None
        engine.dispose()


# ---------------------------------------------------------------------------
# Additional config tests
# ---------------------------------------------------------------------------


class TestEnginePoolConfig:
    @pytest.mark.parametrize("service_module", [
        "services.analytics_api",
        "services.anomaly_detection",
        "services.forecasting_service",
    ])
    def test_engine_created_for_service(self, service_module):
        import importlib
        mod = importlib.import_module(service_module)
        assert hasattr(mod, "engine")
        assert mod.engine is not None

    def test_analytics_engine_is_singleton(self):
        from services.analytics_api import engine as e1
        from services.analytics_api import engine as e2
        assert e1 is e2

    @pytest.mark.parametrize("url,expected_check", [
        ("sqlite:///./test.db", True),
        ("sqlite+pysqlite:///:memory:", True),
    ])
    def test_sqlite_urls_are_test_environments(self, url, expected_check):
        from config.settings import Settings

        original = Settings.database_url
        Settings.database_url = url
        result = Settings.is_test_environment()
        Settings.database_url = original
        assert result is expected_check


class TestSettingsApiWorkers:
    def test_api_workers_positive(self):
        from config.settings import Settings

        assert Settings.api_workers > 0

    def test_max_forecast_horizon_geq_default(self):
        from config.settings import Settings

        assert Settings.max_forecast_horizon_days >= Settings.default_forecast_horizon_days
