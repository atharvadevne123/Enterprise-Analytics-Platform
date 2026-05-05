"""Tests for configuration files and project structure."""

from __future__ import annotations

import os

import pytest
import yaml


class TestConfigFile:
    def test_config_yaml_exists(self):
        assert os.path.exists("config/config.yaml")

    def test_config_yaml_is_valid(self):
        with open("config/config.yaml") as f:
            data = yaml.safe_load(f)
        assert data is not None

    def test_config_yaml_has_content(self):
        with open("config/config.yaml") as f:
            content = f.read()
        assert len(content.strip()) > 0


class TestProjectStructure:
    @pytest.mark.parametrize("path", [
        "services/__init__.py",
        "services/analytics_api.py",
        "services/anomaly_detection.py",
        "services/forecasting_service.py",
        "messaging/__init__.py",
        "messaging/consumer.py",
        "messaging/producer.py",
        "data/__init__.py",
        "data/models.py",
        "spark/load_dimensions.py",
        "spark/calculate_kpis.py",
        "spark/load_facts.py",
        "airflow/dags/etl_batch_dag.py",
        "airflow/dags/data_validation_dag.py",
        "docker/Dockerfile.services",
        "docker-compose.yml",
        "requirements.txt",
        "pyproject.toml",
        "README.md",
    ])
    def test_required_file_exists(self, path):
        assert os.path.exists(path), f"Missing required file: {path}"

    def test_requirements_txt_not_empty(self):
        with open("requirements.txt") as f:
            content = f.read()
        assert len(content.strip()) > 0

    def test_requirements_has_fastapi(self):
        with open("requirements.txt") as f:
            content = f.read()
        assert "fastapi" in content.lower()

    def test_requirements_has_sqlalchemy(self):
        with open("requirements.txt") as f:
            content = f.read()
        assert "sqlalchemy" in content.lower()

    def test_pyproject_toml_valid(self):
        import tomllib
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        assert "project" in data or "build-system" in data


class TestDockerCompose:
    def test_docker_compose_exists(self):
        assert os.path.exists("docker-compose.yml")

    def test_docker_compose_is_valid_yaml(self):
        with open("docker-compose.yml") as f:
            data = yaml.safe_load(f)
        assert data is not None

    def test_docker_compose_has_services(self):
        with open("docker-compose.yml") as f:
            data = yaml.safe_load(f)
        assert "services" in data

    @pytest.mark.parametrize("service", ["postgres", "kafka", "zookeeper"])
    def test_docker_compose_has_required_service(self, service):
        with open("docker-compose.yml") as f:
            content = f.read()
        assert service in content.lower() or service.replace("-", "") in content.lower()
