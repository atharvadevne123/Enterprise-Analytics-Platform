"""
PySpark Job: Load Dimension Tables
Loads and updates dimension tables from staging data
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timedelta

from pyspark.sql import SparkSession
from pyspark.sql.functions import coalesce, col, current_timestamp, lit

logger = logging.getLogger(__name__)

# Initialize Spark session
spark = (
    SparkSession.builder.appName("load-dimensions")
    .config("spark.executor.memory", os.getenv("SPARK_EXECUTOR_MEMORY", "4g"))
    .config("spark.executor.cores", os.getenv("SPARK_EXECUTOR_CORES", "2"))
    .config("spark.shuffle.partitions", "200")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("INFO")

# Database connection properties
db_properties = {
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "password"),
    "driver": "org.postgresql.Driver",
}

db_url = os.getenv(
    "DATABASE_JDBC_URL",
    "jdbc:postgresql://localhost:5432/analytics_warehouse",
)


def load_products_dimension(spark: SparkSession) -> None:
    """Load the products dimension table from staging.

    Performs a full overwrite (SCD Type 1) with warehouse timestamps added.

    Args:
        spark: Active SparkSession to use for reading/writing data.
    """
    logger.info("Loading products dimension...")

    df = spark.read.jdbc(db_url, "staging.stg_products", db_properties)

    df = df.withColumn("dw_created_at", current_timestamp()).withColumn("dw_updated_at", current_timestamp())

    df.write.mode("overwrite").jdbc(db_url, "public.dim_products", db_properties)

    logger.info("Loaded %d products", df.count())


def load_customers_dimension(spark: SparkSession) -> None:
    """Load the customers dimension table, joining lifetime value from orders.

    Args:
        spark: Active SparkSession to use for reading/writing data.
    """
    logger.info("Loading customers dimension...")

    df = spark.read.jdbc(db_url, "staging.stg_customers", db_properties)

    orders_df = spark.read.jdbc(db_url, "staging.stg_orders", db_properties)

    ltv_df = (
        orders_df.groupBy("customer_id")
        .agg({"total_amount": "sum"})
        .withColumnRenamed("sum(total_amount)", "lifetime_value")
    )

    df = (
        df.join(ltv_df, on="customer_id", how="left")
        .withColumn("lifetime_value", coalesce(col("lifetime_value"), lit(0)))
        .withColumn("dw_created_at", current_timestamp())
        .withColumn("dw_updated_at", current_timestamp())
    )

    df.write.mode("overwrite").jdbc(db_url, "public.dim_customers", db_properties)

    logger.info("Loaded %d customers", df.count())


def load_suppliers_dimension(spark: SparkSession) -> None:
    """Load the suppliers dimension table with computed delivery and quality metrics.

    Args:
        spark: Active SparkSession to use for reading/writing data.
    """
    logger.info("Loading suppliers dimension...")

    df = spark.read.jdbc(db_url, "staging.stg_suppliers", db_properties)

    deliveries_df = spark.read.jdbc(db_url, "staging.stg_deliveries", db_properties)

    metrics_df = (
        deliveries_df.groupBy("supplier_id")
        .agg(
            {
                "is_on_time": "avg",
                "is_quality_pass": "avg",
            }
        )
        .withColumnRenamed("avg(is_on_time)", "on_time_delivery_pct")
        .withColumnRenamed("avg(is_quality_pass)", "quality_score")
    )

    df = (
        df.join(metrics_df, on="supplier_id", how="left")
        .withColumn("dw_created_at", current_timestamp())
        .withColumn("dw_updated_at", current_timestamp())
    )

    df.write.mode("overwrite").jdbc(db_url, "public.dim_suppliers", db_properties)

    logger.info("Loaded %d suppliers", df.count())


def load_gl_accounts_dimension(spark: SparkSession) -> None:
    """Load the GL accounts dimension table from staging.

    Args:
        spark: Active SparkSession to use for reading/writing data.
    """
    logger.info("Loading GL accounts dimension...")

    df = spark.read.jdbc(db_url, "staging.stg_gl_accounts", db_properties)

    df = df.withColumn("dw_created_at", current_timestamp())

    df.write.mode("overwrite").jdbc(db_url, "public.dim_gl_accounts", db_properties)

    logger.info("Loaded %d GL accounts", df.count())


def load_date_dimension(spark: SparkSession) -> None:
    """Generate and load the date dimension table for 2020-01-01 to 2030-12-31.

    Intended to be run once (or on demand to extend the range).

    Args:
        spark: Active SparkSession to use for writing data.
    """
    logger.info("Loading date dimension...")

    start_date = datetime(2020, 1, 1)
    end_date = datetime(2030, 12, 31)

    dates = []
    current = start_date

    while current <= end_date:
        dates.append(
            {
                "date_id": int(current.strftime("%Y%m%d")),
                "date": current.date(),
                "year": current.year,
                "quarter": (current.month - 1) // 3 + 1,
                "month": current.month,
                "week": current.isocalendar()[1],
                "day_of_month": current.day,
                "day_of_week": current.weekday() + 1,
                "day_name": current.strftime("%A"),
                "month_name": current.strftime("%B"),
                "is_weekend": 1 if current.weekday() >= 5 else 0,
                "is_holiday": 0,
            }
        )
        current += timedelta(days=1)

    df = spark.createDataFrame(dates)

    df.write.mode("overwrite").jdbc(db_url, "public.dim_dates", db_properties)

    logger.info("Loaded %d dates", df.count())


def main() -> None:
    """Entrypoint — dispatches to the dimension-specific loader.

    Reads the dimension name from sys.argv[1].
    """
    if len(sys.argv) < 2:
        logger.error("Usage: python load_dimensions.py <dimension_name>")
        logger.error("Available dimensions: products, customers, suppliers, gl_accounts, dates")
        sys.exit(1)

    dimension = sys.argv[1]

    try:
        if dimension == "products":
            load_products_dimension(spark)
        elif dimension == "customers":
            load_customers_dimension(spark)
        elif dimension == "suppliers":
            load_suppliers_dimension(spark)
        elif dimension == "gl_accounts":
            load_gl_accounts_dimension(spark)
        elif dimension == "dates":
            load_date_dimension(spark)
        else:
            logger.error("Unknown dimension: %s", dimension)
            sys.exit(1)

        logger.info("Successfully loaded %s dimension", dimension)

    except Exception as e:
        logger.error("Error loading %s: %s", dimension, e, exc_info=True)
        sys.exit(1)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
