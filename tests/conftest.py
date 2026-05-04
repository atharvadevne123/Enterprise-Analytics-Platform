"""Pytest fixtures for Enterprise-Analytics-Platform test suite."""

from __future__ import annotations

import os
from datetime import date
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Environment overrides so services never hit a real DB / Kafka
# ---------------------------------------------------------------------------

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("KAFKA_BROKERS", "localhost:9092")


# ---------------------------------------------------------------------------
# Analytics API fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def analytics_client() -> Generator:
    """TestClient for the analytics API with a mocked DB engine."""
    with patch("services.analytics_api.engine") as mock_engine:
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        from services.analytics_api import app
        with TestClient(app) as client:
            yield client, mock_conn


@pytest.fixture()
def anomaly_client() -> Generator:
    """TestClient for the anomaly detection service with a mocked DB engine."""
    with patch("services.anomaly_detection.engine") as mock_engine:
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        from services.anomaly_detection import app
        with TestClient(app) as client:
            yield client, mock_conn


@pytest.fixture()
def forecasting_client() -> Generator:
    """TestClient for the forecasting service with a mocked DB engine."""
    with patch("services.forecasting_service.engine") as mock_engine:
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        from services.forecasting_service import app
        with TestClient(app) as client:
            yield client, mock_conn


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_ecommerce_row() -> dict:
    return {
        "date": str(date(2024, 1, 15)),
        "total_orders": 1200,
        "total_customers": 850,
        "total_revenue": "95000.50",
        "average_order_value": "79.17",
        "conversion_rate": "3.50",
        "inventory_turnover": "4.20",
    }


@pytest.fixture()
def sample_supply_chain_row() -> dict:
    return {
        "date": str(date(2024, 1, 15)),
        "total_deliveries": 450,
        "on_time_delivery_pct": "94.50",
        "average_lead_time_days": "3.20",
        "supplier_quality_score": "87.30",
    }


@pytest.fixture()
def sample_financial_row() -> dict:
    return {
        "date": str(date(2024, 1, 15)),
        "total_revenue": "150000.00",
        "total_expense": "98000.00",
        "net_income": "52000.00",
        "gross_margin_pct": "34.67",
    }


@pytest.fixture()
def mock_kafka_producer() -> Generator:
    with patch("kafka.producer.KafkaProducer") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture()
def mock_kafka_consumer() -> Generator:
    with patch("kafka.consumer.KafkaConsumer") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_instance
