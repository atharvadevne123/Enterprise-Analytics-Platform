"""
Anomaly Detection Microservice
Detects anomalies in KPI metrics using statistical methods
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import numpy as np
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import create_engine, text

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Anomaly Detection Service",
    description=(
        "Real-time statistical anomaly detection for E-Commerce, Supply Chain, "
        "and Financial KPI metrics using Z-score and IQR methods."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={"name": "Analytics Team", "email": "devneatharva@gmail.com"},
    license_info={"name": "MIT"},
)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Attach a unique X-Request-ID header to every response for tracing."""
    correlation_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    logger.info("Request %s %s [id=%s]", request.method, request.url.path, correlation_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = correlation_id
    return response


# Database connection
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/analytics_warehouse")


def _make_engine(url: str):
    """Create a SQLAlchemy engine appropriate for the dialect."""
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_size=20)


engine = _make_engine(DB_URL)


# Response models
class AnomalyAlert(BaseModel):
    alert_id: str
    severity: str  # CRITICAL, WARNING, INFO
    domain: str
    metric_name: str
    current_value: Decimal
    expected_range_min: Decimal
    expected_range_max: Decimal
    deviation_pct: Decimal
    timestamp: datetime
    recommended_action: str

    class Config:
        json_encoders = {Decimal: str}


# Root
@app.get("/")
def root() -> dict[str, Any]:
    """Return service metadata and available endpoint list."""
    return {
        "service": "anomaly-detection",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/detect/ecommerce/revenue",
            "/detect/ecommerce/conversion-rate",
            "/detect/supply-chain/on-time-delivery",
            "/detect/financial/budget-variance",
            "/alerts/active",
            "/alerts/{alert_id}/acknowledge",
        ],
    }


# Health check
@app.get("/health")
def health_check() -> dict[str, str]:
    """Return service health status."""
    return {"status": "healthy", "service": "anomaly-detection"}


@app.get("/version")
def version() -> dict[str, str]:
    """Return service version information."""
    return {"service": "anomaly-detection", "version": "1.0.0", "python": "3.10+"}


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    """Return basic service metrics."""
    return {
        "service": "anomaly-detection",
        "status": "running",
        "detection_methods": ["z-score", "iqr"],
        "db_pool_size": engine.pool.size(),
    }


@app.get("/readyz")
def readiness() -> dict[str, Any]:
    """Kubernetes readiness probe — verifies DB connection is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "service": "anomaly-detection"}
    except Exception as e:
        logger.error("Readiness check failed: %s", e)
        raise HTTPException(status_code=503, detail="Service not ready")


def detect_statistical_anomaly(
    values: list[float],
    current_value: float,
    threshold_sigma: float = 2.0,
) -> tuple[bool, float, float, float]:
    """Detect anomaly using Z-score method.

    Args:
        values: Historical values for baseline.
        current_value: Current metric value to evaluate.
        threshold_sigma: Number of standard deviations for anomaly threshold.

    Returns:
        Tuple of (is_anomaly, z_score, mean, stddev).
    """
    if len(values) < 3:
        return False, 0.0, 0.0, 0.0

    values_array = np.array(values)
    mean = float(np.mean(values_array))
    stddev = float(np.std(values_array))

    if stddev == 0:
        return False, 0.0, mean, stddev

    z_score = (current_value - mean) / stddev
    is_anomaly = abs(z_score) > threshold_sigma

    return is_anomaly, z_score, mean, stddev


def detect_iqr_anomaly(
    values: list[float],
    current_value: float,
    multiplier: float = 1.5,
) -> tuple[bool, float, float]:
    """Detect anomaly using Interquartile Range (IQR) method.

    Args:
        values: Historical values for baseline.
        current_value: Current metric value to evaluate.
        multiplier: IQR multiplier for fence calculation (1.5 = standard).

    Returns:
        Tuple of (is_anomaly, lower_fence, upper_fence).
    """
    if len(values) < 4:
        return False, 0.0, float("inf")

    values_array = np.array(values)
    q1 = float(np.percentile(values_array, 25))
    q3 = float(np.percentile(values_array, 75))
    iqr = q3 - q1
    lower_fence = q1 - multiplier * iqr
    upper_fence = q3 + multiplier * iqr
    is_anomaly = current_value < lower_fence or current_value > upper_fence

    return is_anomaly, lower_fence, upper_fence


# E-Commerce Anomalies


@app.post("/detect/ecommerce/revenue")
def detect_revenue_anomaly(current_date: date | None = None) -> dict[str, Any]:
    """Detect anomaly in e-commerce revenue"""
    if not current_date:
        current_date = datetime.now().date()

    try:
        with engine.connect() as conn:
            # Get historical data (last 30 days)
            query = text("""
                SELECT total_revenue
                FROM analytics.ecommerce_daily_metrics
                WHERE date < :current_date
                ORDER BY date DESC
                LIMIT 30
            """)

            result = conn.execute(query, {"current_date": current_date})
            historical = [float(row[0]) for row in result]

            # Get current value
            current_query = text("""
                SELECT total_revenue
                FROM analytics.ecommerce_daily_metrics
                WHERE date = :date
            """)

            current_result = conn.execute(current_query, {"date": current_date}).fetchone()

            if not current_result:
                raise HTTPException(status_code=404, detail="No data for date")

            current_value = float(current_result[0])

            # Detect anomaly
            is_anomaly, z_score, mean, stddev = detect_statistical_anomaly(
                historical, current_value, threshold_sigma=2.0
            )

            if is_anomaly:
                deviation_pct = abs((current_value - mean) / mean * 100)
                severity = "CRITICAL" if abs(z_score) > 3 else "WARNING"

                return {
                    "alert_id": f"ecom_revenue_{current_date}",
                    "severity": severity,
                    "domain": "ecommerce",
                    "metric": "revenue",
                    "current_value": current_value,
                    "expected_value": mean,
                    "expected_range_min": mean - (2 * stddev),
                    "expected_range_max": mean + (2 * stddev),
                    "z_score": z_score,
                    "deviation_pct": deviation_pct,
                    "timestamp": datetime.now(),
                    "recommendation": f"Revenue {('↑ up' if current_value > mean else '↓ down')} {deviation_pct:.1f}%. Check for system issues or special events.",
                }
            else:
                return {
                    "alert_id": f"ecom_revenue_{current_date}",
                    "severity": "INFO",
                    "domain": "ecommerce",
                    "metric": "revenue",
                    "current_value": current_value,
                    "expected_value": mean,
                    "deviation_pct": 0,
                    "message": "No anomaly detected",
                }

    except Exception as e:
        logger.error(f"Error detecting revenue anomaly: {e}")
        raise HTTPException(status_code=500, detail="Error detecting anomaly")


@app.post("/detect/ecommerce/conversion-rate")
def detect_conversion_anomaly(current_date: date | None = None) -> dict[str, Any]:
    """Detect anomaly in conversion rate"""
    if not current_date:
        current_date = datetime.now().date()

    try:
        with engine.connect() as conn:
            # Get historical data
            query = text("""
                SELECT conversion_rate
                FROM analytics.ecommerce_daily_metrics
                WHERE date < :current_date
                ORDER BY date DESC
                LIMIT 30
            """)

            result = conn.execute(query, {"current_date": current_date})
            historical = [float(row[0]) for row in result]

            # Get current value
            current_query = text("""
                SELECT conversion_rate
                FROM analytics.ecommerce_daily_metrics
                WHERE date = :date
            """)

            current_result = conn.execute(current_query, {"date": current_date}).fetchone()

            if not current_result:
                raise HTTPException(status_code=404, detail="No data for date")

            current_value = float(current_result[0])

            # Detect anomaly
            is_anomaly, z_score, mean, stddev = detect_statistical_anomaly(
                historical, current_value, threshold_sigma=2.0
            )

            if is_anomaly:
                deviation_pct = abs((current_value - mean) / mean * 100)
                severity = "WARNING"

                return {
                    "alert_id": f"ecom_conv_{current_date}",
                    "severity": severity,
                    "domain": "ecommerce",
                    "metric": "conversion_rate",
                    "current_value": current_value,
                    "expected_value": mean,
                    "deviation_pct": deviation_pct,
                    "timestamp": datetime.now(),
                    "recommendation": "Check website performance, marketing campaigns, or customer experience issues.",
                }

            return {"message": "No anomaly detected"}

    except Exception as e:
        logger.error(f"Error detecting conversion anomaly: {e}")
        raise HTTPException(status_code=500, detail="Error detecting anomaly")


# Supply Chain Anomalies


@app.post("/detect/supply-chain/on-time-delivery")
def detect_delivery_anomaly(current_date: date | None = None) -> dict[str, Any]:
    """Detect anomaly in on-time delivery percentage"""
    if not current_date:
        current_date = datetime.now().date()

    try:
        with engine.connect() as conn:
            # Get historical data
            query = text("""
                SELECT on_time_delivery_pct
                FROM analytics.supply_chain_daily_metrics
                WHERE date < :current_date
                ORDER BY date DESC
                LIMIT 30
            """)

            result = conn.execute(query, {"current_date": current_date})
            historical = [float(row[0]) for row in result]

            # Get current value
            current_query = text("""
                SELECT on_time_delivery_pct
                FROM analytics.supply_chain_daily_metrics
                WHERE date = :date
            """)

            current_result = conn.execute(current_query, {"date": current_date}).fetchone()

            if not current_result:
                raise HTTPException(status_code=404, detail="No data for date")

            current_value = float(current_result[0])

            # Detect anomaly (below expected range is more critical)
            is_anomaly, z_score, mean, stddev = detect_statistical_anomaly(
                historical, current_value, threshold_sigma=1.5
            )

            if is_anomaly and current_value < mean:
                deviation_pct = abs((current_value - mean) / mean * 100)
                severity = "CRITICAL"

                return {
                    "alert_id": f"sc_delivery_{current_date}",
                    "severity": severity,
                    "domain": "supply_chain",
                    "metric": "on_time_delivery_pct",
                    "current_value": current_value,
                    "expected_value": mean,
                    "deviation_pct": deviation_pct,
                    "timestamp": datetime.now(),
                    "recommendation": "Investigate supplier delays. Consider escalation or alternative suppliers.",
                }

            return {"message": "No anomaly detected"}

    except Exception as e:
        logger.error(f"Error detecting delivery anomaly: {e}")
        raise HTTPException(status_code=500, detail="Error detecting anomaly")


# Financial Anomalies


@app.post("/detect/financial/budget-variance")
def detect_budget_variance_anomaly(gl_account_id: str, current_date: date | None = None):
    """Detect anomaly in budget variance"""
    if not current_date:
        current_date = datetime.now().date()

    try:
        with engine.connect() as conn:
            # Get current variance
            query = text("""
                SELECT variance_pct, variance_amount
                FROM public.fact_budget_actuals
                WHERE gl_account_id = :gl_account_id AND date = :date
            """)

            result = conn.execute(query, {"gl_account_id": gl_account_id, "date": current_date}).fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="No budget data for date")

            variance_pct = float(result[0])
            variance_amount = float(result[1])

            # Flag if variance > 10%
            if abs(variance_pct) > 10:
                severity = "CRITICAL" if abs(variance_pct) > 20 else "WARNING"

                return {
                    "alert_id": f"fin_budget_{gl_account_id}_{current_date}",
                    "severity": severity,
                    "domain": "financial",
                    "metric": "budget_variance",
                    "gl_account_id": gl_account_id,
                    "variance_pct": variance_pct,
                    "variance_amount": variance_amount,
                    "timestamp": datetime.now(),
                    "recommendation": f"Investigate budget variance of {variance_pct:.1f}%. Review actual spending patterns.",
                }

            return {"message": "Budget variance within normal range"}

    except Exception as e:
        logger.error(f"Error detecting budget variance: {e}")
        raise HTTPException(status_code=500, detail="Error detecting anomaly")


# Get all active alerts


@app.post("/detect/ecommerce/orders-count")
def detect_orders_count_anomaly(
    current_date: date | None = None,
    method: str = "zscore",
) -> dict[str, Any]:
    """Detect anomaly in daily e-commerce order count using Z-score or IQR method.

    Args:
        current_date: Date to check (defaults to today).
        method: Detection method, one of 'zscore' or 'iqr'.
    """
    if not current_date:
        current_date = datetime.now().date()

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT total_orders
                    FROM analytics.ecommerce_daily_metrics
                    WHERE date < :current_date
                    ORDER BY date DESC LIMIT 30
                """),
                {"current_date": current_date},
            )
            historical = [float(row[0]) for row in result]

            current_result = conn.execute(
                text("""
                    SELECT total_orders FROM analytics.ecommerce_daily_metrics
                    WHERE date = :date
                """),
                {"date": current_date},
            ).fetchone()

            if not current_result:
                raise HTTPException(status_code=404, detail="No data for date")

            current_value = float(current_result[0])

            if method == "iqr":
                is_anomaly, lower, upper = detect_iqr_anomaly(historical, current_value)
                return {
                    "alert_id": f"ecom_orders_{current_date}",
                    "method": "iqr",
                    "is_anomaly": is_anomaly,
                    "current_value": current_value,
                    "lower_fence": lower,
                    "upper_fence": upper,
                    "severity": "WARNING" if is_anomaly else "INFO",
                    "timestamp": datetime.now(),
                }

            is_anomaly, z_score, mean, stddev = detect_statistical_anomaly(historical, current_value)
            return {
                "alert_id": f"ecom_orders_{current_date}",
                "method": "zscore",
                "is_anomaly": is_anomaly,
                "current_value": current_value,
                "mean": mean,
                "z_score": z_score,
                "severity": "CRITICAL" if abs(z_score) > 3 else ("WARNING" if is_anomaly else "INFO"),
                "timestamp": datetime.now(),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error detecting orders count anomaly: %s", e)
        raise HTTPException(status_code=500, detail="Error detecting anomaly")


@app.get("/alerts/active")
def get_active_alerts(
    severity: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """Return all active anomaly alerts, optionally filtered by severity and domain."""
    try:
        # In production, this would query from an alerts table
        # For now, return mock structure

        return {
            "alerts": [],
            "count": 0,
            "timestamp": datetime.now(),
            "filters": {"severity": severity, "domain": domain},
        }

    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail="Error fetching alerts")


@app.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str) -> dict[str, str]:
    """Acknowledge an alert"""
    try:
        return {"alert_id": alert_id, "status": "acknowledged", "timestamp": datetime.now()}

    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail="Error acknowledging alert")


@app.get("/config/settings")
def get_service_settings() -> dict[str, Any]:
    """Return non-sensitive service configuration for diagnostics."""
    try:
        from config.settings import Settings

        return {"service": "anomaly-detection", "config": Settings.as_dict()}
    except Exception as e:
        logger.warning("Settings module not available: %s", e)
        return {"service": "anomaly-detection", "config": {"log_level": "INFO"}}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002, workers=2)
