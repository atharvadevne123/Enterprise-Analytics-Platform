"""Extended tests for Settings class — new attributes and helpers."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from config.settings import Settings


class TestNewSettingsAttributes:
    """Verify newly added settings attributes have correct defaults."""

    def test_max_history_days_default(self):
        assert Settings.max_history_days == 90

    def test_min_anomaly_data_points_default(self):
        assert Settings.min_anomaly_data_points == 10

    def test_max_history_days_env_override(self):
        with patch.dict(os.environ, {"MAX_HISTORY_DAYS": "180"}):
            from importlib import reload
            import config.settings as m
            reload(m)
            assert m.Settings.max_history_days == 180

    def test_min_anomaly_data_points_env_override(self):
        with patch.dict(os.environ, {"MIN_ANOMALY_DATA_POINTS": "20"}):
            from importlib import reload
            import config.settings as m
            reload(m)
            assert m.Settings.min_anomaly_data_points == 20


class TestGetKafkaTopics:
    """Verify get_kafka_topics returns well-formed topic names."""

    def test_returns_list(self):
        topics = Settings.get_kafka_topics()
        assert isinstance(topics, list)

    def test_returns_nine_topics(self):
        assert len(Settings.get_kafka_topics()) == 9

    def test_all_topics_have_dot_separator(self):
        for topic in Settings.get_kafka_topics():
            assert "." in topic, f"Topic '{topic}' missing domain prefix"

    @pytest.mark.parametrize("expected_topic", [
        "ecommerce.orders",
        "supply_chain.deliveries",
        "financials.transactions",
    ])
    def test_expected_topics_present(self, expected_topic):
        assert expected_topic in Settings.get_kafka_topics()

    def test_no_duplicate_topics(self):
        topics = Settings.get_kafka_topics()
        assert len(topics) == len(set(topics))


class TestSettingsPackageImport:
    """Verify the config package exposes Settings correctly."""

    def test_import_from_config_package(self):
        from config import Settings as S
        assert S is not None

    def test_settings_singleton_from_package(self):
        from config import settings as s
        assert s is not None

    def test_settings_singleton_is_settings_instance(self):
        from config import Settings, settings
        assert isinstance(settings, Settings)

    def test_as_dict_includes_new_keys(self):
        d = Settings.as_dict()
        assert "kafka_brokers" in d
        assert "zscore_threshold" in d
