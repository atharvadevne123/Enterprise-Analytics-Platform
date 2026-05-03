"""Microservices for the Unified Enterprise Analytics Platform.

Each submodule is a standalone FastAPI application exposing REST endpoints
for analytics queries, demand forecasting, and anomaly detection.
"""

from __future__ import annotations

__all__ = [
    "analytics_api",
    "forecasting_service",
    "anomaly_detection",
]

__version__ = "1.0.0"
