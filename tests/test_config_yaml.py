"""Tests for config/config.yaml structure and validity."""

from __future__ import annotations

import pytest


class TestConfigYamlStructure:
    """Verify top-level sections exist in config.yaml."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open("config/config.yaml") as f:
            self._content = f.read()

    @pytest.mark.parametrize("section", [
        "kafka",
        "database",
        "airflow",
        "spark",
        "services",
        "monitoring",
        "features",
    ])
    def test_top_level_section_present(self, section):
        assert section + ":" in self._content

    def test_kafka_topics_defined(self):
        assert "topics:" in self._content

    def test_database_warehouse_host_placeholder(self):
        assert "${DB_HOST}" in self._content

    def test_spark_shuffle_partitions_set(self):
        assert "shuffle_partitions" in self._content

    def test_monitoring_prometheus_enabled(self):
        assert "prometheus:" in self._content

    def test_services_analytics_port(self):
        assert "8000" in self._content

    def test_features_anomaly_detection_flag(self):
        assert "anomaly_detection:" in self._content

    def test_rate_limiting_section(self):
        assert "rate_limiting" in self._content

    def test_caching_section(self):
        assert "caching" in self._content

    def test_security_cors_section(self):
        assert "cors_origins" in self._content


class TestConfigYamlKafkaTopics:
    """Verify Kafka topic names follow naming conventions."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open("config/config.yaml") as f:
            self._content = f.read()

    @pytest.mark.parametrize("topic_fragment", [
        "ecommerce.orders",
        "supply_chain.deliveries",
        "financials.transactions",
    ])
    def test_expected_topic_present(self, topic_fragment):
        assert topic_fragment in self._content

    def test_consumer_group_defined(self):
        assert "consumer_group" in self._content

    def test_batch_size_defined(self):
        assert "batch_size" in self._content


class TestConfigYamlAirflow:
    """Verify Airflow schedule cron expressions are present."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open("config/config.yaml") as f:
            self._content = f.read()

    def test_daily_midnight_schedule(self):
        assert "0 0 * * *" in self._content

    def test_etl_schedule_present(self):
        assert "etl_batch" in self._content

    def test_forecasting_schedule_weekly(self):
        assert "0 4 * * 0" in self._content

    def test_dags_folder_configured(self):
        assert "dags_folder" in self._content
