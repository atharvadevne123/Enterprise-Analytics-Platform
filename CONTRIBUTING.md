# Contributing to Enterprise Analytics Platform

## Getting Started

1. Fork the repository and clone your fork.
2. Install dependencies: `make install`
3. Install pre-commit hooks: `make pre-commit-install`
4. Copy `.env.example` to `.env` and fill in your values.

## Development Workflow

```bash
# Run tests
make test

# Lint and auto-fix
make lint-fix

# Type check
make type-check

# Start a service locally
make run-analytics
```

## Pull Request Guidelines

- Keep PRs focused: one feature or fix per PR.
- Run `make lint` and `make test` before submitting.
- Write tests for any new functionality.
- Update `CHANGELOG.md` with a summary of your change.

## Code Style

- Python 3.10+ type annotations required on all public functions.
- Google-style docstrings on all classes and public methods.
- Use `logging.getLogger(__name__)` — no bare `print()` calls.
- Line length: 120 characters (configured in `pyproject.toml`).

## Testing

- New features must include unit tests in `tests/`.
- Aim for ≥80% coverage on service modules.
- Mock external dependencies (DB, Kafka) — tests must run offline.

## Commit Message Format

```
type(scope): short description

Optional longer body.
```

Types: `feat`, `fix`, `test`, `ci`, `docs`, `chore`, `refactor`, `perf`.

## Reporting Issues

Open an issue with a clear title, steps to reproduce, and expected vs. actual behavior.
