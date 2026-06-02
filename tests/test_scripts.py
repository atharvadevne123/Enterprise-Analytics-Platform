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


class TestGenerateSampleDataScript:
    def test_generate_sample_data_module_importable(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("generate_sample_data", "scripts/generate_sample_data.py")
        assert spec is not None

    def test_generate_sample_data_has_main(self):
        with open("scripts/generate_sample_data.py") as f:
            content = f.read()
        assert "def main" in content
        assert "write_ecommerce" in content
        assert "write_supply_chain" in content
        assert "write_financial" in content

    def test_generate_sample_data_writes_csvs(self, tmp_path):
        import importlib.util

        spec = importlib.util.spec_from_file_location("generate_sample_data", "scripts/generate_sample_data.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        from pathlib import Path

        out = Path(tmp_path)
        mod.write_ecommerce(out, 5)
        mod.write_supply_chain(out, 5)
        mod.write_financial(out, 5)
        assert (out / "ecommerce_daily_metrics.csv").exists()
        assert (out / "supply_chain_daily_metrics.csv").exists()
        assert (out / "financial_daily_metrics.csv").exists()

    def test_generate_sample_data_row_count(self, tmp_path):
        import csv as csv_module
        import importlib.util
        from pathlib import Path

        spec = importlib.util.spec_from_file_location("generate_sample_data", "scripts/generate_sample_data.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = Path(tmp_path)
        mod.write_ecommerce(out, 10)
        with (out / "ecommerce_daily_metrics.csv").open() as f:
            rows = list(csv_module.DictReader(f))
        assert len(rows) == 10

    @pytest.mark.parametrize("rows", [1, 5, 30])
    def test_generate_sample_data_parametrized_rows(self, tmp_path, rows):
        import importlib.util
        from pathlib import Path

        spec = importlib.util.spec_from_file_location("generate_sample_data", "scripts/generate_sample_data.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = Path(tmp_path)
        mod.write_financial(out, rows)
        import csv as csv_module

        with (out / "financial_daily_metrics.csv").open() as f:
            assert len(list(csv_module.DictReader(f))) == rows


# ---------------------------------------------------------------------------
# Additional script tests
# ---------------------------------------------------------------------------


class TestValidateEnvScript:
    def test_parse_env_example_returns_list(self, tmp_path):
        from scripts.validate_env import parse_env_example

        env_file = tmp_path / ".env.example"
        env_file.write_text("DATABASE_URL=postgresql://localhost/db\nKAFKA_BROKERS=localhost:9092\n")
        result = parse_env_example(str(env_file))
        assert "DATABASE_URL" in result
        assert "KAFKA_BROKERS" in result

    def test_parse_env_example_ignores_comments(self, tmp_path):
        from scripts.validate_env import parse_env_example

        env_file = tmp_path / ".env.example"
        env_file.write_text("# This is a comment\nACTUAL_VAR=value\n")
        result = parse_env_example(str(env_file))
        assert "ACTUAL_VAR" in result
        assert len([r for r in result if "comment" in r.lower()]) == 0

    def test_parse_env_example_missing_file(self):
        from scripts.validate_env import parse_env_example

        result = parse_env_example("/nonexistent/.env.example")
        assert result == []

    def test_check_env_vars_detects_set_vars(self, monkeypatch):
        from scripts.validate_env import check_env_vars

        monkeypatch.setenv("MY_TEST_VAR", "hello")
        results = dict(check_env_vars(["MY_TEST_VAR", "UNSET_VAR_XYZ"]))
        assert results["MY_TEST_VAR"] is True
        assert results["UNSET_VAR_XYZ"] is False


class TestGenerateSampleDataScript:
    def test_write_ecommerce_creates_file(self, tmp_path):
        from scripts.generate_sample_data import write_ecommerce

        path = write_ecommerce(tmp_path, 5)
        assert path.exists()
        with open(path) as f:
            lines = f.readlines()
        assert len(lines) == 6  # header + 5 rows

    def test_write_financial_creates_file(self, tmp_path):
        from scripts.generate_sample_data import write_financial

        path = write_financial(tmp_path, 3)
        assert path.exists()

    def test_write_supply_chain_creates_file(self, tmp_path):
        from scripts.generate_sample_data import write_supply_chain

        path = write_supply_chain(tmp_path, 4)
        assert path.exists()
        with open(path) as f:
            lines = f.readlines()
        assert len(lines) == 5  # header + 4 rows
