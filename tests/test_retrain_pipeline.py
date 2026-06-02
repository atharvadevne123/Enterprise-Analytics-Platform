"""Tests for the ETL batch and data validation DAG pipeline structure."""

from __future__ import annotations

import pytest


class TestETLBatchDAG:
    def test_etl_dag_file_parseable(self):
        """ETL batch DAG file should parse without syntax errors."""
        with open("airflow/dags/etl_batch_dag.py") as f:
            content = f.read()
        compile(content, "etl_batch_dag.py", "exec")

    def test_etl_dag_has_schedule(self):
        with open("airflow/dags/etl_batch_dag.py") as f:
            content = f.read()
        assert "schedule_interval" in content or "schedule" in content

    def test_etl_dag_has_catchup_false(self):
        with open("airflow/dags/etl_batch_dag.py") as f:
            content = f.read()
        assert "catchup=False" in content

    def test_etl_dag_defines_load_audit_task(self):
        with open("airflow/dags/etl_batch_dag.py") as f:
            content = f.read()
        assert "load_etl_audit" in content or "audit" in content.lower()

    @pytest.mark.parametrize("dag_id", ["etl_batch_processing"])
    def test_etl_dag_id_present(self, dag_id):
        with open("airflow/dags/etl_batch_dag.py") as f:
            content = f.read()
        assert dag_id in content


class TestDataValidationDAG:
    def test_validation_dag_file_parseable(self):
        with open("airflow/dags/data_validation_dag.py") as f:
            content = f.read()
        compile(content, "data_validation_dag.py", "exec")

    def test_validation_dag_has_validation_functions(self):
        with open("airflow/dags/data_validation_dag.py") as f:
            content = f.read()
        for func in ["validate_orders_table", "validate_transactions_table"]:
            assert func in content

    def test_validation_dag_daily_schedule(self):
        with open("airflow/dags/data_validation_dag.py") as f:
            content = f.read()
        assert "0 0 * * *" in content or "daily" in content.lower()

    @pytest.mark.parametrize("tag", ["data-quality", "validation"])
    def test_validation_dag_has_tags(self, tag):
        with open("airflow/dags/data_validation_dag.py") as f:
            content = f.read()
        assert tag in content

    def test_record_validation_status_function_exists(self):
        with open("airflow/dags/data_validation_dag.py") as f:
            content = f.read()
        assert "record_validation_status" in content


# ---------------------------------------------------------------------------
# Additional retrain pipeline tests
# ---------------------------------------------------------------------------


class TestPipelineOrchestration:
    def test_etl_dag_uses_spark_submit(self):
        with open("airflow/dags/etl_batch_dag.py") as f:
            content = f.read()
        assert "SparkSubmit" in content or "spark" in content.lower()

    def test_validation_dag_uses_python_operator(self):
        with open("airflow/dags/data_validation_dag.py") as f:
            content = f.read()
        assert "PythonOperator" in content or "python_callable" in content

    @pytest.mark.parametrize("required_import", [
        "from airflow import DAG",
        "from airflow.operators",
    ])
    def test_etl_dag_required_imports(self, required_import):
        with open("airflow/dags/etl_batch_dag.py") as f:
            content = f.read()
        assert required_import in content

    def test_both_dags_have_default_args(self):
        for dag_file in ["airflow/dags/etl_batch_dag.py", "airflow/dags/data_validation_dag.py"]:
            with open(dag_file) as f:
                content = f.read()
            assert "default_args" in content
            assert "retries" in content
