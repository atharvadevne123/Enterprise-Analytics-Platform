# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x.x   | yes       |

## Reporting a Vulnerability

Please do not open a public GitHub issue for security vulnerabilities.

Email devneatharva@gmail.com with:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigations

You will receive a response within 48 hours. Confirmed vulnerabilities will be patched and released promptly.

## Security Best Practices

- Never commit secrets, credentials, or API keys to the repository.
- Use `.env` files (excluded by `.gitignore`) for all secrets.
- Always reference `.env.example` for required environment variables.
- Database credentials must use `os.getenv()` — never hardcoded defaults in production.
- All SQL queries use parameterized statements (SQLAlchemy `text()` with bound parameters).
- FastAPI input validation via Pydantic models on all endpoints.
- Kafka producer/consumer use `acks='all'` for durability.

## Dependency Updates

Dependabot is enabled and automatically creates PRs for dependency updates. Review and merge these promptly to stay current with security patches.

