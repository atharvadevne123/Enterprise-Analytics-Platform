# Contributing to Enterprise Analytics Platform

## Architecture Overview

The platform is composed of three FastAPI microservices, a Kafka streaming layer,
Apache Spark ETL jobs, and Airflow DAGs — all backed by a PostgreSQL analytics warehouse.

```
┌──────────────────────────────────────────────────────┐
│                   FastAPI Services                   │
│  analytics_api (:8000) │ anomaly (:8001) │ forecast  │
└────────────────────────┬─────────────────────────────┘
                         │ SQLAlchemy
                    ┌────▼────┐
                    │ Postgres │  ◄──  Spark ETL  ◄──  Kafka
                    └─────────┘                        │
                                               Airflow DAGs
```

## Getting Started

1. Fork the repository and clone your fork.
2. Install dependencies: `make install-dev`
3. Install pre-commit hooks: `make pre-commit-install`
4. Copy `.env.example` to `.env` and fill in your values.

## Development Workflow

```bash
# Run unit tests with coverage
make test

# Run integration tests (requires running services)
make test-integration

# Lint and auto-fix
make lint-fix

# Format code
make format

# Type check
make type-check

# Security scan
make security

# Generate HTML coverage report
make coverage

# Start a service locally
make run-analytics   # :8000
make run-anomaly     # :8001
make run-forecasting # :8002
```

## Pull Request Guidelines

- Keep PRs focused: one feature or fix per PR.
- Run `make lint && make test` before submitting.
- Write tests for any new functionality.
- Update `CHANGELOG.md` under `[Unreleased]` with your change.
- Add `@pytest.mark.integration` to any test that requires live services.

## Code Style

- Python 3.10+ type annotations required on all public functions.
- Google-style docstrings on all classes and public methods.
- Use `logging.getLogger(__name__)` — no bare `print()` calls.
- Line length: 120 characters (configured in `pyproject.toml`).
- Ruff rules: E, F, W, I, UP, B, SIM.

## Testing

- New features must include unit tests in `tests/`.
- Aim for ≥80% coverage on service modules.
- Mock external dependencies (DB, Kafka) — unit tests must run offline.
- Use `pytest.mark.parametrize` for data-driven tests.

## Commit Message Format

```
type(scope): short description

Optional longer body.
```

Types: `feat`, `fix`, `test`, `ci`, `docs`, `chore`, `refactor`, `perf`.

Scope examples: `analytics-api`, `anomaly`, `forecasting`, `kafka`, `spark`, `airflow`.

## Adding a New Endpoint

1. Add the route function to the appropriate service file under `services/`.
2. Add a Pydantic response model if the schema is non-trivial.
3. Add parametrized tests in the corresponding `tests/test_*.py` file.
4. Update the `endpoints` list in the service `root()` function.
5. Update `CHANGELOG.md`.

## Configuration Validation

Run `Settings.validate()` after any change to environment variables:

```python
from config.settings import Settings
errors = Settings.validate()
if errors:
    for e in errors:
        print(f"[CONFIG ERROR] {e}")
```

Or via the CLI helper:

```bash
make validate-env
```

## Adding a New Setting

1. Add the class attribute to `config/settings.py` with a sensible default.
2. Document the variable in `.env.example` with a comment.
3. Add the variable to the `README.md` Environment Variables table.
4. Write tests in `tests/test_settings_extended.py` covering the default and override.

## Reporting Issues

Open an issue with a clear title, steps to reproduce, and expected vs. actual behavior.
Include the service name, endpoint path, and any relevant log output.
