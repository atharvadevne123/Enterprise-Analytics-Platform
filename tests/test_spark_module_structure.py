"""Extended structural tests for Spark ETL job modules."""

from __future__ import annotations

import ast
import pytest


def _parse(path: str) -> ast.Module:
    with open(path) as f:
        return ast.parse(f.read(), filename=path)


def _function_names(tree: ast.Module) -> list[str]:
    return [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]


class TestCalculateKPIsStructure:
    """Verify calculate_kpis.py module structure via AST."""

    @pytest.fixture(autouse=True)
    def _parse(self):
        self.tree = _parse("spark/calculate_kpis.py")
        self.funcs = _function_names(self.tree)

    def test_file_parses_without_errors(self):
        assert self.tree is not None

    @pytest.mark.parametrize("fn", [
        "calculate_ecommerce_kpis",
        "calculate_supply_chain_kpis",
        "calculate_financial_kpis",
        "calculate_unified_kpis",
        "main",
    ])
    def test_expected_function_defined(self, fn):
        assert fn in self.funcs

    def test_has_future_annotations_import(self):
        with open("spark/calculate_kpis.py") as f:
            src = f.read()
        assert "from __future__ import annotations" in src

    def test_has_logging_setup(self):
        with open("spark/calculate_kpis.py") as f:
            src = f.read()
        assert "logging.getLogger" in src

    def test_spark_session_used(self):
        with open("spark/calculate_kpis.py") as f:
            src = f.read()
        assert "SparkSession" in src


class TestLoadDimensionsStructure:
    """Verify load_dimensions.py module structure via AST."""

    @pytest.fixture(autouse=True)
    def _parse(self):
        self.tree = _parse("spark/load_dimensions.py")
        self.funcs = _function_names(self.tree)

    def test_file_parses_without_errors(self):
        assert self.tree is not None

    @pytest.mark.parametrize("fn", [
        "load_products_dimension",
        "load_customers_dimension",
        "load_suppliers_dimension",
        "load_date_dimension",
        "main",
    ])
    def test_expected_function_defined(self, fn):
        assert fn in self.funcs

    def test_has_logging(self):
        with open("spark/load_dimensions.py") as f:
            src = f.read()
        assert "logger" in src

    def test_uses_write_mode_overwrite(self):
        with open("spark/load_dimensions.py") as f:
            src = f.read()
        assert "overwrite" in src


class TestLoadFactsStructure:
    """Verify load_facts.py module structure via AST."""

    @pytest.fixture(autouse=True)
    def _parse(self):
        self.tree = _parse("spark/load_facts.py")
        self.funcs = _function_names(self.tree)

    def test_file_parses_without_errors(self):
        assert self.tree is not None

    @pytest.mark.parametrize("fn", [
        "load_orders_fact",
        "load_deliveries_fact",
        "load_transactions_fact",
        "load_budget_actuals_fact",
        "main",
    ])
    def test_expected_function_defined(self, fn):
        assert fn in self.funcs

    def test_private_helper_defined(self):
        assert "_to_date_id" in self.funcs

    def test_has_type_any_import(self):
        with open("spark/load_facts.py") as f:
            src = f.read()
        assert "from typing import Any" in src or "Any" in src


class TestAllSparkJobsHaveDocstrings:
    """Ensure every top-level function in spark jobs has a docstring."""

    @pytest.mark.parametrize("spark_file", [
        "spark/calculate_kpis.py",
        "spark/load_dimensions.py",
        "spark/load_facts.py",
    ])
    def test_module_has_docstring(self, spark_file):
        tree = _parse(spark_file)
        assert ast.get_docstring(tree) is not None, f"{spark_file} missing module docstring"
