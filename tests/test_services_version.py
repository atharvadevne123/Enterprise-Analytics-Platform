"""Tests for services package version and service name constants."""

from __future__ import annotations

import pytest


class TestServicesVersion:
    """Verify __version__ is correctly defined and formatted."""

    def test_version_importable(self):
        from services import __version__

        assert __version__ is not None

    def test_version_is_string(self):
        from services import __version__

        assert isinstance(__version__, str)

    def test_version_follows_semver_pattern(self):
        from services import __version__

        parts = __version__.split(".")
        assert len(parts) >= 2
        assert parts[0].isdigit()

    def test_version_matches_pyproject(self):
        """__version__ should match the version declared in pyproject.toml."""
        from services import __version__

        with open("pyproject.toml") as f:
            content = f.read()
        assert f'version = "{__version__}"' in content


class TestServicesServiceNames:
    """Verify SERVICE_NAMES constant is correct."""

    def test_service_names_importable(self):
        from services import SERVICE_NAMES

        assert SERVICE_NAMES is not None

    def test_service_names_is_list(self):
        from services import SERVICE_NAMES

        assert isinstance(SERVICE_NAMES, list)

    def test_service_names_has_three_entries(self):
        from services import SERVICE_NAMES

        assert len(SERVICE_NAMES) == 3

    @pytest.mark.parametrize(
        "name",
        [
            "analytics_api",
            "anomaly_detection",
            "forecasting_service",
        ],
    )
    def test_expected_service_name_present(self, name):
        from services import SERVICE_NAMES

        assert name in SERVICE_NAMES

    def test_service_names_all_unique(self):
        from services import SERVICE_NAMES

        assert len(SERVICE_NAMES) == len(set(SERVICE_NAMES))


class TestServicesAllExports:
    """Verify __all__ covers version and service names."""

    def test_all_defined(self):
        import services

        assert hasattr(services, "__all__")

    def test_version_in_all(self):
        import services

        assert "__version__" in services.__all__

    def test_service_names_in_all(self):
        import services

        assert "SERVICE_NAMES" in services.__all__
