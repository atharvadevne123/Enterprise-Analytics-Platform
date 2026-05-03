"""Tests for utility scripts."""

from __future__ import annotations

import os
import sys

import pytest


class TestHealthCheckScript:
    def test_health_check_module_importable(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("health_check", "scripts/health_check.py")
        assert spec is not None

    def test_health_check_has_main(self):
        with open("scripts/health_check.py") as f:
            content = f.read()
        assert "def main" in content
        assert "check_service" in content

    def test_health_check_services_defined(self):
        with open("scripts/health_check.py") as f:
            content = f.read()
        assert "analytics-api" in content
        assert "forecasting-service" in content
        assert "anomaly-detection" in content

    @pytest.mark.parametrize("port", [8000, 8001, 8002])
    def test_health_check_covers_ports(self, port):
        with open("scripts/health_check.py") as f:
            content = f.read()
        assert str(port) in content


class TestValidateEnvScript:
    def test_validate_env_module_importable(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("validate_env", "scripts/validate_env.py")
        assert spec is not None

    def test_validate_env_has_parse_function(self):
        with open("scripts/validate_env.py") as f:
            content = f.read()
        assert "parse_env_example" in content
        assert "check_env_vars" in content

    def test_validate_env_reads_env_example(self):
        with open("scripts/validate_env.py") as f:
            content = f.read()
        assert ".env.example" in content

    def test_parse_env_example_function(self, tmp_path):
        env_file = tmp_path / ".env.example"
        env_file.write_text("DATABASE_URL=postgres://...\nKAFKA_BROKERS=localhost:9092\n# comment\n")
        sys.path.insert(0, str(os.getcwd()))
        import importlib.util
        spec = importlib.util.spec_from_file_location("validate_env", "scripts/validate_env.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        vars_found = mod.parse_env_example(str(env_file))
        assert "DATABASE_URL" in vars_found
        assert "KAFKA_BROKERS" in vars_found

    def test_check_env_vars_detects_missing(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("validate_env", "scripts/validate_env.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        results = mod.check_env_vars(["DEFINITELY_NOT_SET_VAR_XYZ123"])
        assert results[0] == ("DEFINITELY_NOT_SET_VAR_XYZ123", False)

    def test_check_env_vars_detects_present(self):
        import importlib.util
        os.environ["TEST_VAR_ABC123"] = "test_value"
        spec = importlib.util.spec_from_file_location("validate_env", "scripts/validate_env.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        results = mod.check_env_vars(["TEST_VAR_ABC123"])
        assert results[0] == ("TEST_VAR_ABC123", True)
        del os.environ["TEST_VAR_ABC123"]
