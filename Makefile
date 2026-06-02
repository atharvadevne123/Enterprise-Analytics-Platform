.PHONY: install install-dev test test-all test-integration lint lint-fix format format-check type-check coverage security run-analytics run-anomaly run-forecasting docker-build docker-up docker-down docker-logs clean pre-commit-install validate-env health-check help

install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest pytest-cov ruff mypy httpx pre-commit

install-dev: install
	pip install scikit-learn statsmodels scipy kafka-python-ng
	pip install bandit[toml] types-PyYAML

test:
	pytest tests/ -v --tb=short \
		--cov=services --cov=messaging --cov=data \
		--cov-report=term-missing \
		--ignore=tests/test_spark_jobs.py

test-all:
	pytest tests/ -v --tb=short

test-integration:
	pytest tests/ -v --tb=short -m integration

coverage:
	pytest tests/ --cov=services --cov=messaging --cov=data \
		--cov-report=html --cov-report=term-missing \
		--ignore=tests/test_spark_jobs.py
	@echo "Coverage report: htmlcov/index.html"

lint:
	ruff check .
	ruff format --check .

lint-fix:
	ruff check . --fix
	ruff format .

format:
	ruff format .

format-check:
	ruff format --check .

type-check:
	mypy services/ --ignore-missing-imports --no-error-summary

security:
	bandit -r services/ messaging/ data/ -ll --exit-zero

run-analytics:
	uvicorn services.analytics_api:app --host 0.0.0.0 --port 8000 --reload

run-anomaly:
	uvicorn services.anomaly_detection:app --host 0.0.0.0 --port 8001 --reload

run-forecasting:
	uvicorn services.forecasting_service:app --host 0.0.0.0 --port 8002 --reload

docker-build:
	docker build -f docker/Dockerfile.services -t enterprise-analytics:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov dist build *.egg-info coverage.xml

pre-commit-install:
	pre-commit install

validate-env:
	python scripts/validate_env.py

health-check:
	python scripts/health_check.py

help:
	@echo "Available targets:"
	@echo "  install          Install runtime dependencies"
	@echo "  install-dev      Install all dev dependencies"
	@echo "  test             Run tests with coverage (unit only)"
	@echo "  test-all         Run all tests including integration"
	@echo "  test-integration Run only integration-marked tests"
	@echo "  coverage         Generate HTML coverage report"
	@echo "  lint             Check code with ruff (check + format)"
	@echo "  lint-fix         Auto-fix ruff issues"
	@echo "  format           Format code with ruff"
	@echo "  format-check     Check formatting without modifying files"
	@echo "  type-check       Run mypy type checker"
	@echo "  security         Run bandit security scanner"
	@echo "  run-analytics    Start analytics API on :8000"
	@echo "  run-anomaly      Start anomaly detection on :8001"
	@echo "  run-forecasting  Start forecasting service on :8002"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-up        Start all services via docker-compose"
	@echo "  docker-down      Stop all services"
	@echo "  docker-logs      Tail docker-compose logs"
	@echo "  clean            Remove build artifacts and caches"
	@echo "  validate-env     Validate required environment variables"
	@echo "  health-check     Check health of all running services"
