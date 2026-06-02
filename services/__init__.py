"""FastAPI microservices for the Enterprise Analytics Platform.

Three independent services are provided:

- ``analytics_api``: KPI queries across e-commerce, supply chain, and financial domains.
- ``anomaly_detection``: Z-score and IQR-based statistical anomaly alerts.
- ``forecasting_service``: ARIMA and linear-regression demand/lead-time/cash-flow forecasts.

Each service exposes ``/health``, ``/version``, and ``/metrics`` endpoints in addition
to its domain-specific routes.
"""

from __future__ import annotations

#: Shared version string aligned with pyproject.toml.
__version__ = "1.1.0"

#: Canonical list of service module names in this package.
SERVICE_NAMES: list[str] = ["analytics_api", "anomaly_detection", "forecasting_service"]

__all__ = ["analytics_api", "anomaly_detection", "forecasting_service", "__version__", "SERVICE_NAMES"]
