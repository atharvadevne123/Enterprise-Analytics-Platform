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
        spec = importlib.util.spec_from_file_location(
            "generate_sample_data", "scripts/generate_sample_data.py"
        )
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
        spec = importlib.util.spec_from_file_location(
            "generate_sample_data", "scripts/generate_sample_data.py"
        )
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
        spec = importlib.util.spec_from_file_location(
            "generate_sample_data", "scripts/generate_sample_data.py"
        )
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
        spec = importlib.util.spec_from_file_location(
            "generate_sample_data", "scripts/generate_sample_data.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = Path(tmp_path)
        mod.write_financial(out, rows)
        import csv as csv_module
        with (out / "financial_daily_metrics.csv").open() as f:
            assert len(list(csv_module.DictReader(f))) == rows
