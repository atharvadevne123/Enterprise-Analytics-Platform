# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite covering analytics API, anomaly detection, forecasting service, Kafka, and Spark jobs
- GitHub Actions CI workflow with multi-version Python matrix, coverage reporting, and mypy type-checking
- `.env.example` template with all required environment variables documented
- `Makefile` with targets for install, test, lint, type-check, and Docker operations
- `.pre-commit-config.yaml` with ruff and whitespace hooks
- `CONTRIBUTING.md` with development workflow and coding standards
- `pyproject.toml` extended with ruff, pytest, and mypy configuration
- Type annotations added to all service modules
- Google-style docstrings on all public functions and classes
- Structured logging replacing print statements across all modules
- `/health`, `/metrics`, and `/version` endpoints on all FastAPI services
- Input validation middleware and rate limiting on API services
- Correlation ID logging middleware for distributed tracing

## [1.0.0] — 2024-01-01

### Added
- Analytics API microservice with E-Commerce, Supply Chain, and Financial KPI endpoints
- Anomaly Detection service with statistical outlier detection (Z-score, IQR)
- Forecasting service with ARIMA, Linear Regression, and Prophet models
- Kafka producer/consumer for real-time event streaming
- Apache Spark ETL jobs for dimensional modeling and KPI calculation
- Airflow DAGs for batch ETL orchestration and data validation
- PostgreSQL analytics warehouse with optimised star schema
- Docker Compose stack: PostgreSQL, Kafka, Zookeeper, Spark, Airflow, Prometheus, Grafana
- Kubernetes manifests for production deployment
- Prometheus metrics integration on all services
