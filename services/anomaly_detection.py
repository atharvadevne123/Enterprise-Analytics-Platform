"""
Anomaly Detection Microservice
Detects anomalies in KPI metrics using statistical methods
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import FastAPI, HTTPException
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

# Database connection
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/analytics_warehouse"
)

engine = create_engine(DB_URL, pool_size=20)


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
def root() -> Dict[str, Any]:
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
            "/alerts/{alert_id}/acknowledge"
        ]
    }


# Health check
@app.get("/health")
def health_check() -> Dict[str, str]:
    """Return service health status."""
    return {"status": "healthy", "service": "anomaly-detection"}


@app.get("/version")
def version() -> Dict[str, str]:
    """Return service version information."""
    return {"service": "anomaly-detection", "version": "1.0.0", "python": "3.10+"}


@app.get("/metrics")
def metrics() -> Dict[str, Any]:
    """Return basic service metrics."""
    return {
        "service": "anomaly-detection",
        "status": "running",
        "detection_methods": ["z-score", "iqr"],
        "db_pool_size": engine.pool.size(),
    }


def detect_statistical_anomaly(
    values: List[float],
    current_value: float,
    threshold_sigma: float = 2.0
) -> tuple:
    """
    Detect anomaly using Z-score method

    Args:
        values: Historical values
        current_value: Current metric value
        threshold_sigma: Number of standard deviations

    Returns:
        (is_anomaly, z_score, mean, stddev)
    """
    if len(values) < 3:
        return False, 0, 0, 0

    values_array = np.array(values)
    mean = np.mean(values_array)
    stddev = np.std(values_array)

    if stddev == 0:
        return False, 0, mean, stddev

    z_score = (current_value - mean) / stddev
    is_anomaly = abs(z_score) > threshold_sigma

    return is_anomaly, z_score, mean, stddev


# E-Commerce Anomalies

@app.post("/detect/ecommerce/revenue")
def detect_revenue_anomaly(current_date: Optional[date] = None) -> Dict[str, Any]:
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

            current_result = conn.execute(
                current_query,
                {"date": current_date}
            ).fetchone()

            if not current_result:
                raise HTTPException(status_code=404, detail="No data for date")

            current_value = float(current_result[0])

            # Detect anomaly
            is_anomaly, z_score, mean, stddev = detect_statistical_anomaly(
                historical,
                current_value,
                threshold_sigma=2.0
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
                    "recommendation": f"Revenue {('↑ up' if current_value > mean else '↓ down')} {deviation_pct:.1f}%. Check for system issues or special events."
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
                    "message": "No anomaly detected"
                }

    except Exception as e:
        logger.error(f"Error detecting revenue anomaly: {e}")
        raise HTTPException(status_code=500, detail="Error detecting anomaly")


@app.post("/detect/ecommerce/conversion-rate")
def detect_conversion_anomaly(current_date: Optional[date] = None) -> Dict[str, Any]:
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

            current_result = conn.execute(
                current_query,
                {"date": current_date}
            ).fetchone()

            if not current_result:
                raise HTTPException(status_code=404, detail="No data for date")

            current_value = float(current_result[0])

            # Detect anomaly
            is_anomaly, z_score, mean, stddev = detect_statistical_anomaly(
                historical,
                current_value,
                threshold_sigma=2.0
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
                    "recommendation": "Check website performance, marketing campaigns, or customer experience issues."
                }

            return {"message": "No anomaly detected"}

    except Exception as e:
        logger.error(f"Error detecting conversion anomaly: {e}")
        raise HTTPException(status_code=500, detail="Error detecting anomaly")


# Supply Chain Anomalies

@app.post("/detect/supply-chain/on-time-delivery")
def detect_delivery_anomaly(current_date: Optional[date] = None) -> Dict[str, Any]:
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

            current_result = conn.execute(
                current_query,
                {"date": current_date}
            ).fetchone()

            if not current_result:
                raise HTTPException(status_code=404, detail="No data for date")

            current_value = float(current_result[0])

            # Detect anomaly (below expected range is more critical)
            is_anomaly, z_score, mean, stddev = detect_statistical_anomaly(
                historical,
                current_value,
                threshold_sigma=1.5
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
                    "recommendation": "Investigate supplier delays. Consider escalation or alternative suppliers."
                }

            return {"message": "No anomaly detected"}

    except Exception as e:
        logger.error(f"Error detecting delivery anomaly: {e}")
        raise HTTPException(status_code=500, detail="Error detecting anomaly")


# Financial Anomalies

@app.post("/detect/financial/budget-variance")
def detect_budget_variance_anomaly(
    gl_account_id: str,
    current_date: Optional[date] = None
):
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

            result = conn.execute(
                query,
                {"gl_account_id": gl_account_id, "date": current_date}
            ).fetchone()

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
                    "recommendation": f"Investigate budget variance of {variance_pct:.1f}%. Review actual spending patterns."
                }

            return {"message": "Budget variance within normal range"}

    except Exception as e:
        logger.error(f"Error detecting budget variance: {e}")
        raise HTTPException(status_code=500, detail="Error detecting anomaly")


# Get all active alerts

@app.get("/alerts/active")
def get_active_alerts(
    severity: Optional[str] = None,
    domain: Optional[str] = None,
) -> Dict[str, Any]:
    """Return all active anomaly alerts, optionally filtered by severity and domain."""
    try:
        # In production, this would query from an alerts table
        # For now, return mock structure

        return {
            "alerts": [],
            "count": 0,
            "timestamp": datetime.now(),
            "filters": {
                "severity": severity,
                "domain": domain
            }
        }

    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail="Error fetching alerts")


@app.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str) -> Dict[str, str]:
    """Acknowledge an alert"""
    try:
        return {
            "alert_id": alert_id,
            "status": "acknowledged",
            "timestamp": datetime.now()
        }

    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail="Error acknowledging alert")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, workers=2)
