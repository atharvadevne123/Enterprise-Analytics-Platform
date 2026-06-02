# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `Settings.validate()` method — surfaces misconfigured thresholds and out-of-range ports as a list of human-readable error strings
- `Settings.get_kafka_topics()` helper — returns the canonical nine-topic list for all domains
- `Settings.max_history_days` and `Settings.min_anomaly_data_points` environment-variable-backed attributes
- `MAX_HISTORY_DAYS` and `MIN_ANOMALY_DATA_POINTS` variables added to `.env.example`
- `__version__` and `SERVICE_NAMES` constants exported from the `services` package
- `Settings` and `settings` singleton re-exported from `config` package `__init__`
- `tests/test_config_yaml.py` — YAML structure, Kafka topic naming, and Airflow schedule validation
- `tests/test_spark_module_structure.py` — AST-based structural tests for all three Spark ETL modules
- `tests/test_settings_extended.py` — tests for new settings attributes and `get_kafka_topics`
- `tests/test_settings_validate.py` — threshold and port validation edge cases
- `tests/test_services_package.py` — package interface, module existence, and endpoint presence tests
- `tests/test_data_package.py` — data model importability, inheritance, and KPI/forecast model tests
- `tests/test_messaging_init.py` — messaging package export and class attribute tests
- Additional parametrized tests for all service modules (analytics_api, anomaly_detection, forecasting_service)
- Cross-service header consistency integration tests
- OpenAPI docs accessibility and error-handling tests
- Expanded Kafka producer/consumer test coverage with edge cases
- Additional data model validation tests for Supplier, GLAccount, UnifiedKPIMetrics
- New fixtures: sample_order_event, sample_delivery_event, sample_date_range

### Changed
- Replaced `print()` calls in all scripts with structured `logging`
- Improved docstrings for all API endpoint functions
- Tightened return type annotations across service modules and DAGs
- Expanded `CONTRIBUTING.md` with configuration validation workflow and adding-new-setting guide

## [1.2.0-dev] — (next release)

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
