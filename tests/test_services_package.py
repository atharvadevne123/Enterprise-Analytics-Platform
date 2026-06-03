"""Tests for the services package public interface."""

from __future__ import annotations

import ast
import os

import pytest


class TestServicesPackageDocstring:
    """Verify services/__init__.py has an informative docstring and __all__."""

    @pytest.fixture(autouse=True)
    def _read(self):
        with open("services/__init__.py") as f:
            self._src = f.read()
        self._tree = ast.parse(self._src)

    def test_module_has_docstring(self):
        assert ast.get_docstring(self._tree) is not None

    def test_docstring_mentions_analytics_api(self):
        assert "analytics_api" in self._src

    def test_docstring_mentions_anomaly_detection(self):
        assert "anomaly_detection" in self._src

    def test_docstring_mentions_forecasting_service(self):
        assert "forecasting_service" in self._src

    def test_all_defined(self):
        assert "__all__" in self._src


class TestServicesModuleFiles:
    """Ensure every declared service module file actually exists."""

    @pytest.mark.parametrize(
        "filename",
        [
            "services/analytics_api.py",
            "services/anomaly_detection.py",
            "services/forecasting_service.py",
        ],
    )
    def test_service_file_exists(self, filename):
        assert os.path.isfile(filename)

    @pytest.mark.parametrize(
        "filename",
        [
            "services/analytics_api.py",
            "services/anomaly_detection.py",
            "services/forecasting_service.py",
        ],
    )
    def test_service_file_parseable(self, filename):
        with open(filename) as f:
            src = f.read()
        compile(src, filename, "exec")


class TestServicesModuleHealthEndpoints:
    """Every service must define a /health route handler."""

    @pytest.mark.parametrize(
        "service_file",
        [
            "services/analytics_api.py",
            "services/anomaly_detection.py",
            "services/forecasting_service.py",
        ],
    )
    def test_health_endpoint_defined(self, service_file):
        with open(service_file) as f:
            src = f.read()
        assert "/health" in src

    @pytest.mark.parametrize(
        "service_file",
        [
            "services/analytics_api.py",
            "services/anomaly_detection.py",
            "services/forecasting_service.py",
        ],
    )
    def test_version_endpoint_defined(self, service_file):
        with open(service_file) as f:
            src = f.read()
        assert "/version" in src

    @pytest.mark.parametrize(
        "service_file",
        [
            "services/analytics_api.py",
            "services/anomaly_detection.py",
            "services/forecasting_service.py",
        ],
    )
    def test_metrics_endpoint_defined(self, service_file):
        with open(service_file) as f:
            src = f.read()
        assert "/metrics" in src
