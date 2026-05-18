# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `/ecommerce/top-products` endpoint returning top N products by revenue
- `/supply-chain/inventory-risk` endpoint flagging products below reorder point
- `/financial/cash-position` endpoint reporting current cash balance
- `/detect/financial/cashflow` anomaly detection endpoint for cash flow metrics
- `/detect/supply-chain/lead-time` anomaly detection endpoint for supplier lead times
- `/forecast/inventory/reorder` endpoint predicting when reorder triggers will fire
- `/forecast/demand/trend` endpoint exposing linear trend coefficients
- Bandit security scanning in CI (`make security`)
- `install-dev` Makefile target for complete dev environment setup
- `coverage` Makefile target producing HTML coverage report
- `format` and `format-check` Makefile targets
- `test-integration` Makefile target for integration-only test runs
- Centralized service configuration in `config/settings.py`

### Changed
- CI actions updated to `actions/checkout@v4`, `actions/setup-python@v5`, `actions/upload-artifact@v4`
- Ruff lint step now uses `pyproject.toml` config (no inline flags needed)
- Makefile `lint` target now also checks formatting via `ruff format --check`

### Fixed
- `MultiTopicConsumer` missing return type annotation on `consume_messages`
- `UnifiedConsumer.close` and `MultiTopicConsumer.close` now typed `-> None`

## [1.1.0] — 2025-05-18

### Added
- Comprehensive test suite covering analytics API, anomaly detection, forecasting service, Kafka, and Spark jobs
- GitHub Actions CI workflow with multi-version Python matrix (3.10, 3.11, 3.12), coverage reporting, and mypy type-checking
- Makefile with targets for install, test, lint, type-check, and Docker operations
- `.pre-commit-config.yaml` with ruff and whitespace hooks
- `CONTRIBUTING.md` with development workflow and coding standards
- `pyproject.toml` extended with ruff B/SIM rules, pytest markers, and mypy strict settings
- Type annotations on all service modules and messaging layer
- Google-style docstrings on all public functions and classes across all modules
- Structured logging replacing print statements across all modules
- `/health`, `/metrics`, `/version`, and `/readyz` endpoints on all FastAPI services
- Correlation ID middleware (`X-Request-ID`) on all three FastAPI services
- IQR-based anomaly detection alongside existing Z-score detector
- `detect_iqr_anomaly()` helper function in anomaly detection service
- `/detect/ecommerce/orders-count` endpoint supporting both `zscore` and `iqr` detection methods
- `_make_engine()` dialect helper in all three FastAPI services (SQLite + PostgreSQL)
- PySpark job type annotations and structured logging
- Airflow DAG function return types and expanded docstrings

### Changed
- ARIMA forecasting falls back to moving average on convergence failure (logged as WARNING)
- Engine pool size increased to 20 in analytics API and forecasting service
- Ruff lint now selects E, F, W, I, UP, B, SIM rules with E501/B008/SIM117 ignored

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
