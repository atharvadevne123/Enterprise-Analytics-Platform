"""
Centralized service configuration loaded from environment variables.
"""

from __future__ import annotations

import os


class Settings:
    """Application settings derived from environment variables."""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/analytics_warehouse",
    )

    # Kafka
    kafka_brokers: list[str] = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")
    kafka_group_id: str = os.getenv("KAFKA_GROUP_ID", "unified-analytics")

    # Service ports
    analytics_api_port: int = int(os.getenv("ANALYTICS_API_PORT", "8000"))
    anomaly_detection_port: int = int(os.getenv("ANOMALY_DETECTION_PORT", "8001"))
    forecasting_service_port: int = int(os.getenv("FORECASTING_SERVICE_PORT", "8002"))

    # Forecasting
    default_forecast_horizon_days: int = int(os.getenv("DEFAULT_FORECAST_HORIZON", "30"))
    max_forecast_horizon_days: int = int(os.getenv("MAX_FORECAST_HORIZON", "365"))

    # Anomaly detection
    zscore_threshold: float = float(os.getenv("ZSCORE_THRESHOLD", "2.0"))
    iqr_multiplier: float = float(os.getenv("IQR_MULTIPLIER", "1.5"))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Workers
    api_workers: int = int(os.getenv("API_WORKERS", "4"))

    @classmethod
    def is_test_environment(cls) -> bool:
        """Return True when DATABASE_URL points to SQLite (test mode)."""
        return cls.database_url.startswith("sqlite")

    @classmethod
    def as_dict(cls) -> dict:
        """Return a sanitized dict of all settings (no secrets)."""
        return {
            "database_url": cls.database_url.split("@")[-1] if "@" in cls.database_url else "sqlite",
            "kafka_brokers": cls.kafka_brokers,
            "kafka_group_id": cls.kafka_group_id,
            "analytics_api_port": cls.analytics_api_port,
            "anomaly_detection_port": cls.anomaly_detection_port,
            "forecasting_service_port": cls.forecasting_service_port,
            "default_forecast_horizon_days": cls.default_forecast_horizon_days,
            "zscore_threshold": cls.zscore_threshold,
            "iqr_multiplier": cls.iqr_multiplier,
            "log_level": cls.log_level,
            "is_test": cls.is_test_environment(),
        }


settings = Settings()
