"""FastAPI microservices for the Enterprise Analytics Platform.

Three independent services are provided:

- ``analytics_api``: KPI queries across e-commerce, supply chain, and financial domains.
- ``anomaly_detection``: Z-score and IQR-based statistical anomaly alerts.
- ``forecasting_service``: ARIMA and linear-regression demand/lead-time/cash-flow forecasts.

Each service exposes ``/health``, ``/version``, and ``/metrics`` endpoints in addition
to its domain-specific routes.
"""

from __future__ import annotations

__all__ = ["analytics_api", "anomaly_detection", "forecasting_service"]
