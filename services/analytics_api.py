"""
Analytics API Microservice
FastAPI service for querying KPI metrics and analytics
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import create_engine, text

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Unified Analytics API",
    description=(
        "Real-time analytics and KPI queries for E-Commerce, Supply Chain, "
        "and Financial Intelligence across the enterprise data warehouse."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={"name": "Analytics Team", "email": "devneatharva@gmail.com"},
    license_info={"name": "MIT"},
)

# Database connection
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/analytics_warehouse"
)

engine = create_engine(DB_URL, pool_size=20, max_overflow=40)


# Request validation models
class DateRangeRequest(BaseModel):
    """Validated date range for analytics queries."""

    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def end_must_be_after_start(cls, end: date, info: Any) -> date:
        """Ensure end_date is not before start_date."""
        start = info.data.get("start_date")
        if start and end < start:
            raise ValueError("end_date must be >= start_date")
        return end


# Response models
class KPIMetric(BaseModel):
    date: date
    metric_name: str
    value: Decimal
    target: Optional[Decimal] = None
    variance_pct: Optional[Decimal] = None

    class Config:
        json_encoders = {Decimal: str}


class ECommerceMetrics(BaseModel):
    date: date
    total_orders: int
    total_customers: int
    total_revenue: Decimal
    average_order_value: Decimal
    conversion_rate: Decimal
    inventory_turnover: Decimal

    class Config:
        json_encoders = {Decimal: str}


class SupplyChainMetrics(BaseModel):
    date: date
    total_deliveries: int
    on_time_delivery_pct: Decimal
    average_lead_time_days: Decimal
    supplier_quality_score: Decimal

    class Config:
        json_encoders = {Decimal: str}


class FinancialMetrics(BaseModel):
    date: date
    total_revenue: Decimal
    total_expense: Decimal
    net_income: Decimal
    gross_margin_pct: Decimal

    class Config:
        json_encoders = {Decimal: str}


class UnifiedKPIs(BaseModel):
    date: date
    revenue_per_supplier: Decimal
    profit_per_product: Decimal
    order_to_cash_cycle_days: int
    cash_conversion_cycle_days: int

    class Config:
        json_encoders = {Decimal: str}


# Root
@app.get("/")
def root() -> Dict[str, Any]:
    """Return service metadata and available endpoint list."""
    return {
        "service": "analytics-api",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/ecommerce/metrics/{start_date}/{end_date}",
            "/ecommerce/conversion-rate",
            "/supply-chain/metrics/{start_date}/{end_date}",
            "/supply-chain/supplier/{supplier_id}/performance",
            "/financial/metrics/{start_date}/{end_date}",
            "/financial/budget-vs-actual/{gl_account_id}",
            "/kpis/unified/{start_date}/{end_date}",
            "/kpis/summary"
        ]
    }


# Health check
@app.get("/health")
def health_check() -> Dict[str, str]:
    """Return service health status."""
    return {"status": "healthy", "service": "analytics-api"}


@app.get("/version")
def version() -> Dict[str, str]:
    """Return service version information."""
    return {"service": "analytics-api", "version": "1.0.0", "python": "3.10+"}


@app.get("/metrics")
def metrics() -> Dict[str, Any]:
    """Return basic service metrics."""
    return {
        "service": "analytics-api",
        "status": "running",
        "endpoints_available": 8,
        "db_pool_size": engine.pool.size(),
    }


# E-Commerce Endpoints

@app.get("/ecommerce/metrics/{start_date}/{end_date}",
         response_model=List[ECommerceMetrics])
def get_ecommerce_metrics(
    start_date: date,
    end_date: date,
    granularity: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
) -> List[Dict[str, Any]]:
    """Get e-commerce KPI metrics for date range"""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT
                    date,
                    total_orders,
                    total_customers,
                    total_revenue,
                    average_order_value,
                    conversion_rate,
                    inventory_turnover
                FROM analytics.ecommerce_daily_metrics
                WHERE date BETWEEN :start_date AND :end_date
                ORDER BY date DESC
            """)

            result = conn.execute(
                query,
                {"start_date": start_date, "end_date": end_date}
            )

            metrics = [dict(row._mapping) for row in result]
            return metrics

    except Exception as e:
        logger.error(f"Error fetching e-commerce metrics: {e}")
        raise HTTPException(status_code=500, detail="Error fetching metrics")


@app.get("/ecommerce/conversion-rate")
def get_conversion_rate(
    days: int = Query(30, ge=1, le=365),
) -> Dict[str, Any]:
    """Get conversion rate for last N days"""
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        with engine.connect() as conn:
            query = text("""
                SELECT
                    AVG(conversion_rate) as avg_conversion_rate,
                    MIN(conversion_rate) as min_conversion_rate,
                    MAX(conversion_rate) as max_conversion_rate,
                    STDDEV(conversion_rate) as stddev_conversion_rate
                FROM analytics.ecommerce_daily_metrics
                WHERE date BETWEEN :start_date AND :end_date
            """)

            result = conn.execute(
                query,
                {"start_date": start_date, "end_date": end_date}
            ).fetchone()

            return {
                "period_days": days,
                "average": float(result[0]) if result[0] else 0,
                "minimum": float(result[1]) if result[1] else 0,
                "maximum": float(result[2]) if result[2] else 0,
                "stddev": float(result[3]) if result[3] else 0
            }

    except Exception as e:
        logger.error(f"Error calculating conversion rate: {e}")
        raise HTTPException(status_code=500, detail="Error calculating conversion rate")


# Supply Chain Endpoints

@app.get("/supply-chain/metrics/{start_date}/{end_date}",
         response_model=List[SupplyChainMetrics])
def get_supply_chain_metrics(
    start_date: date,
    end_date: date,
) -> List[Dict[str, Any]]:
    """Get supply chain KPI metrics"""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT
                    date,
                    total_deliveries,
                    on_time_delivery_pct,
                    average_lead_time_days,
                    supplier_quality_score
                FROM analytics.supply_chain_daily_metrics
                WHERE date BETWEEN :start_date AND :end_date
                ORDER BY date DESC
            """)

            result = conn.execute(
                query,
                {"start_date": start_date, "end_date": end_date}
            )

            metrics = [dict(row._mapping) for row in result]
            return metrics

    except Exception as e:
        logger.error(f"Error fetching supply chain metrics: {e}")
        raise HTTPException(status_code=500, detail="Error fetching metrics")


@app.get("/supply-chain/supplier/{supplier_id}/performance")
def get_supplier_performance(supplier_id: int) -> Dict[str, Any]:
    """Get supplier performance metrics"""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT
                    supplier_id,
                    supplier_name,
                    on_time_delivery_pct,
                    quality_score,
                    lead_time_days
                FROM public.dim_suppliers
                WHERE supplier_id = :supplier_id
            """)

            result = conn.execute(
                query,
                {"supplier_id": supplier_id}
            ).fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Supplier not found")

            return {
                "supplier_id": result[0],
                "supplier_name": result[1],
                "on_time_delivery_pct": float(result[2]),
                "quality_score": float(result[3]),
                "lead_time_days": result[4]
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching supplier performance: {e}")
        raise HTTPException(status_code=500, detail="Error fetching supplier data")


# Financial Endpoints

@app.get("/financial/metrics/{start_date}/{end_date}",
         response_model=List[FinancialMetrics])
def get_financial_metrics(
    start_date: date,
    end_date: date,
) -> List[Dict[str, Any]]:
    """Get financial KPI metrics"""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT
                    date,
                    total_revenue,
                    total_expense,
                    net_income,
                    gross_margin_pct
                FROM analytics.financial_daily_metrics
                WHERE date BETWEEN :start_date AND :end_date
                ORDER BY date DESC
            """)

            result = conn.execute(
                query,
                {"start_date": start_date, "end_date": end_date}
            )

            metrics = [dict(row._mapping) for row in result]
            return metrics

    except Exception as e:
        logger.error(f"Error fetching financial metrics: {e}")
        raise HTTPException(status_code=500, detail="Error fetching metrics")


@app.get("/financial/budget-vs-actual/{gl_account_id}")
def get_budget_vs_actual(
    gl_account_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> Dict[str, Any]:
    """Get budget vs actual comparison"""
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).date()
    if not end_date:
        end_date = datetime.now().date()

    try:
        with engine.connect() as conn:
            query = text("""
                SELECT
                    date,
                    budget_amount,
                    actual_amount,
                    variance_amount,
                    variance_pct
                FROM public.fact_budget_actuals
                WHERE gl_account_id = :gl_account_id
                    AND date BETWEEN :start_date AND :end_date
                ORDER BY date
            """)

            result = conn.execute(
                query,
                {
                    "gl_account_id": gl_account_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )

            data = [dict(row._mapping) for row in result]
            return {
                "gl_account_id": gl_account_id,
                "period": {"start": start_date, "end": end_date},
                "data": data
            }

    except Exception as e:
        logger.error(f"Error fetching budget vs actual: {e}")
        raise HTTPException(status_code=500, detail="Error fetching budget data")


# Unified KPI Endpoints

@app.get("/kpis/unified/{start_date}/{end_date}",
         response_model=List[UnifiedKPIs])
def get_unified_kpis(
    start_date: date,
    end_date: date,
) -> List[Dict[str, Any]]:
    """Get unified cross-domain KPIs"""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT
                    date,
                    revenue_per_supplier,
                    profit_per_product,
                    order_to_cash_cycle_days,
                    cash_conversion_cycle_days
                FROM analytics.unified_kpi_metrics
                WHERE date BETWEEN :start_date AND :end_date
                ORDER BY date DESC
            """)

            result = conn.execute(
                query,
                {"start_date": start_date, "end_date": end_date}
            )

            metrics = [dict(row._mapping) for row in result]
            return metrics

    except Exception as e:
        logger.error(f"Error fetching unified KPIs: {e}")
        raise HTTPException(status_code=500, detail="Error fetching KPIs")


@app.get("/kpis/summary")
def get_kpi_summary() -> Dict[str, Any]:
    """Get current KPI summary — uses most recent date that has data"""
    try:
        with engine.connect() as conn:
            # Find most recent date with e-commerce data
            latest = conn.execute(
                text("""
                SELECT date FROM analytics.ecommerce_daily_metrics
                WHERE total_orders > 0 ORDER BY date DESC LIMIT 1
                """)
            ).fetchone()
            end_date = latest[0] if latest else datetime.now().date()

            ecom = conn.execute(
                text("""
                SELECT total_revenue, average_order_value, conversion_rate
                FROM analytics.ecommerce_daily_metrics
                WHERE date = :date
                """),
                {"date": end_date}
            ).fetchone()

            sc = conn.execute(
                text("""
                SELECT on_time_delivery_pct, average_lead_time_days
                FROM analytics.supply_chain_daily_metrics
                WHERE date = :date
                """),
                {"date": end_date}
            ).fetchone()

            fin = conn.execute(
                text("""
                SELECT net_income, gross_margin_pct
                FROM analytics.financial_daily_metrics
                WHERE date = :date
                """),
                {"date": end_date}
            ).fetchone()

            return {
                "date": end_date,
                "ecommerce": {
                    "revenue": float(ecom[0]) if ecom else 0,
                    "aov": float(ecom[1]) if ecom else 0,
                    "conversion_rate": float(ecom[2]) if ecom else 0
                },
                "supply_chain": {
                    "on_time_pct": float(sc[0]) if sc else 0,
                    "lead_time_days": float(sc[1]) if sc else 0
                },
                "financial": {
                    "net_income": float(fin[0]) if fin else 0,
                    "margin_pct": float(fin[1]) if fin else 0
                }
            }

    except Exception as e:
        logger.error(f"Error fetching KPI summary: {e}")
        raise HTTPException(status_code=500, detail="Error fetching summary")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=4)
