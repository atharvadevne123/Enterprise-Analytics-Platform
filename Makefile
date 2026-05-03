.PHONY: install test lint type-check run docker-build docker-up docker-down clean help

install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest pytest-cov ruff mypy httpx pre-commit

test:
	pytest tests/ -v --tb=short \
		--cov=services --cov=kafka --cov=data \
		--cov-report=term-missing \
		--ignore=tests/test_spark_jobs.py

test-all:
	pytest tests/ -v --tb=short

lint:
	ruff check . --select E,F,W,I --ignore E501
	ruff format --check .

lint-fix:
	ruff check . --select E,F,W,I --ignore E501 --fix
	ruff format .

type-check:
	mypy services/ --ignore-missing-imports --no-error-summary

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
	rm -rf .pytest_cache .mypy_cache .ruff_cache dist build *.egg-info

pre-commit-install:
	pre-commit install

help:
	@echo "Available targets:"
	@echo "  install          Install all dependencies"
	@echo "  test             Run tests with coverage"
	@echo "  lint             Check code with ruff"
	@echo "  lint-fix         Auto-fix ruff issues"
	@echo "  type-check       Run mypy type checker"
	@echo "  run-analytics    Start analytics API on :8000"
	@echo "  run-anomaly      Start anomaly detection on :8001"
	@echo "  run-forecasting  Start forecasting service on :8002"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-up        Start all services via docker-compose"
	@echo "  docker-down      Stop all services"
	@echo "  clean            Remove build artifacts and caches"
