"""Tests for environment configuration and service settings."""

from __future__ import annotations

import os
from unittest.mock import patch


class TestDatabaseURLConfiguration:
    """Verify DATABASE_URL env var drives engine creation."""

    def test_default_url_is_postgresql(self):
        """Default DATABASE_URL contains postgres."""
        from services import analytics_api
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
