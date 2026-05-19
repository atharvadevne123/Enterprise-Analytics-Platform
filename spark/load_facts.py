"""
PySpark Job: Load Fact Tables
Loads order, delivery, and transaction facts from staging
"""

from __future__ import annotations

import logging
import os
import sys

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp
from pyspark.sql.functions import round as spark_round

logger = logging.getLogger(__name__)

# Initialize Spark session
spark = (
    SparkSession.builder.appName("load-facts")
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


def _to_date_id(col_name: str):
    """Return a Spark column expression converting a date column to YYYYMMDD int."""
    return spark_round(col(col_name).cast("date").cast("string").regexp_replace("-", "").cast("int"))


def load_orders_fact(spark: SparkSession) -> None:
    """Load the orders fact table from staging.stg_orders.

    Adds derived columns: gross_profit, gross_margin_pct, and warehouse timestamps.

    Args:
        spark: Active SparkSession to use for reading/writing data.
    """
    logger.info("Loading orders fact table...")

    orders = spark.read.jdbc(db_url, "staging.stg_orders", db_properties)

    orders = orders.withColumn("order_date_id", _to_date_id("order_date"))

    orders = (
        orders.withColumn("gross_profit", col("order_amount") - col("cost_amount"))
        .withColumn("gross_margin_pct", spark_round((col("gross_profit") / col("order_amount")) * 100, 2))
        .withColumn("dw_created_at", current_timestamp())
        .withColumn("dw_updated_at", current_timestamp())
    )

    fact_columns = [
        "order_id",
        "order_date_id",
        "customer_id",
        "product_id",
        "supplier_id",
        "quantity",
        "list_price",
        "discount_amount",
        "order_amount",
        "tax_amount",
        "shipping_amount",
        "total_amount",
        "cost_amount",
        "gross_profit",
        "gross_margin_pct",
        "order_status",
        "payment_status",
        "shipping_status",
        "created_at",
        "dw_created_at",
        "dw_updated_at",
    ]

    orders.select(*fact_columns).write.mode("append").jdbc(db_url, "public.fact_orders", db_properties)

    logger.info("Loaded %d orders", orders.count())


def load_deliveries_fact(spark: SparkSession) -> None:
    """Load the deliveries fact table from staging.stg_deliveries.

    Adds lead_time_days and is_on_time derived columns.

    Args:
        spark: Active SparkSession to use for reading/writing data.
    """
    logger.info("Loading deliveries fact table...")

    deliveries = spark.read.jdbc(db_url, "staging.stg_deliveries", db_properties)

    deliveries = (
        deliveries.withColumn("order_date_id", _to_date_id("order_date"))
        .withColumn("delivery_date_id", _to_date_id("delivery_date"))
        .withColumn("promised_date_id", _to_date_id("promised_date"))
    )

    deliveries = (
        deliveries.withColumn("lead_time_days", (col("delivery_date").cast("date") - col("order_date").cast("date")))
        .withColumn("is_on_time", col("delivery_date") <= col("promised_date"))
        .withColumn("dw_created_at", current_timestamp())
        .withColumn("dw_updated_at", current_timestamp())
    )

    fact_columns = [
        "delivery_id",
        "po_id",
        "supplier_id",
        "product_id",
        "order_date_id",
        "delivery_date_id",
        "promised_date_id",
        "quantity_ordered",
        "quantity_delivered",
        "quantity_rejected",
        "unit_cost",
        "total_cost",
        "lead_time_days",
        "is_on_time",
        "is_quality_pass",
        "delivery_status",
        "created_at",
        "dw_created_at",
        "dw_updated_at",
    ]

    deliveries.select(*fact_columns).write.mode("append").jdbc(db_url, "public.fact_deliveries", db_properties)

    logger.info("Loaded %d deliveries", deliveries.count())


def load_transactions_fact(spark: SparkSession) -> None:
    """Load the transactions fact table from staging.stg_transactions.

    Adds net_amount and warehouse timestamp columns.

    Args:
        spark: Active SparkSession to use for reading/writing data.
    """
    logger.info("Loading transactions fact table...")

    transactions = spark.read.jdbc(db_url, "staging.stg_transactions", db_properties)

    transactions = (
        transactions.withColumn("transaction_date_id", _to_date_id("transaction_date"))
        .withColumn("net_amount", col("debit_amount") - col("credit_amount"))
        .withColumn("dw_created_at", current_timestamp())
        .withColumn("dw_updated_at", current_timestamp())
    )

    fact_columns = [
        "transaction_id",
        "transaction_date_id",
        "gl_account_id",
        "debit_amount",
        "credit_amount",
        "net_amount",
        "transaction_type",
        "description",
        "reference_id",
        "currency_code",
        "exchange_rate",
        "is_intercompany",
        "is_reconciled",
        "created_at",
        "dw_created_at",
        "dw_updated_at",
    ]

    transactions.select(*fact_columns).write.mode("append").jdbc(db_url, "public.fact_transactions", db_properties)

    logger.info("Loaded %d transactions", transactions.count())


def load_budget_actuals_fact(spark: SparkSession) -> None:
    """Load the budget vs actuals fact table by joining staging budgets and actuals.

    Calculates variance_amount and variance_pct derived columns.

    Args:
        spark: Active SparkSession to use for reading/writing data.
    """
    logger.info("Loading budget vs actuals fact table...")

    budgets = spark.read.jdbc(db_url, "staging.stg_budgets", db_properties).withColumn(
        "date_id", _to_date_id("budget_date")
    )

    actuals = spark.read.jdbc(db_url, "staging.stg_actuals", db_properties).withColumn(
        "date_id", _to_date_id("actual_date")
    )

    budget_actuals = (
        budgets.join(actuals, on=["gl_account_id", "date_id"], how="full")
        .withColumn("variance_amount", col("actual_amount") - col("budget_amount"))
        .withColumn("variance_pct", spark_round((col("variance_amount") / col("budget_amount")) * 100, 2))
        .withColumn("dw_created_at", current_timestamp())
        .withColumn("dw_updated_at", current_timestamp())
    )

    budget_actuals.write.mode("append").jdbc(db_url, "public.fact_budget_actuals", db_properties)

    logger.info("Loaded %d budget vs actuals records", budget_actuals.count())


def main() -> None:
    """Entrypoint — dispatches to the fact-specific loader.

    Reads the fact table name from sys.argv[1].
    """
    if len(sys.argv) < 2:
        logger.error("Usage: python load_facts.py <fact_name>")
        logger.error("Available facts: orders, deliveries, transactions, budget_actuals")
        sys.exit(1)

    fact = sys.argv[1]

    try:
        if fact == "orders":
            load_orders_fact(spark)
        elif fact == "deliveries":
            load_deliveries_fact(spark)
        elif fact == "transactions":
            load_transactions_fact(spark)
        elif fact == "budget_actuals":
            load_budget_actuals_fact(spark)
        else:
            logger.error("Unknown fact: %s", fact)
            sys.exit(1)

        logger.info("Successfully loaded %s fact table", fact)

    except Exception as e:
        logger.error("Error loading %s: %s", fact, e, exc_info=True)
        sys.exit(1)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
