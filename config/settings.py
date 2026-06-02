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

    # Anomaly history window
    max_history_days: int = int(os.getenv("MAX_HISTORY_DAYS", "90"))

    # Minimum data points required before running anomaly detection
    min_anomaly_data_points: int = int(os.getenv("MIN_ANOMALY_DATA_POINTS", "10"))

    @classmethod
    def is_test_environment(cls) -> bool:
        """Return True when DATABASE_URL points to SQLite (test mode)."""
        return cls.database_url.startswith("sqlite")

    @classmethod
    def get_kafka_topics(cls) -> list[str]:
        """Return the canonical list of Kafka topics for all domains."""
        return [
            "ecommerce.orders",
            "ecommerce.inventory",
            "ecommerce.customers",
            "supply_chain.suppliers",
            "supply_chain.deliveries",
            "supply_chain.purchase_orders",
            "financials.transactions",
            "financials.budgets",
            "financials.actuals",
        ]

    @classmethod
    def validate(cls) -> list[str]:
        """Return a list of configuration validation errors (empty if valid).

        Checks that numeric thresholds are positive and ports are in valid range.
        """
        errors: list[str] = []
        if cls.zscore_threshold <= 0:
            errors.append(f"ZSCORE_THRESHOLD must be positive, got {cls.zscore_threshold}")
        if cls.iqr_multiplier <= 0:
            errors.append(f"IQR_MULTIPLIER must be positive, got {cls.iqr_multiplier}")
        if cls.max_history_days < 1:
            errors.append(f"MAX_HISTORY_DAYS must be >= 1, got {cls.max_history_days}")
        if cls.min_anomaly_data_points < 1:
            errors.append(f"MIN_ANOMALY_DATA_POINTS must be >= 1, got {cls.min_anomaly_data_points}")
        for name, port in [
            ("ANALYTICS_API_PORT", cls.analytics_api_port),
            ("ANOMALY_DETECTION_PORT", cls.anomaly_detection_port),
            ("FORECASTING_SERVICE_PORT", cls.forecasting_service_port),
        ]:
            if not (1 <= port <= 65535):
                errors.append(f"{name} must be 1-65535, got {port}")
        return errors

    @classmethod
    def as_dict(cls) -> dict[str, object]:
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
