"""
PySpark Job: Load Fact Tables
Loads order, delivery, and transaction facts from staging
"""

import sys

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp
from pyspark.sql.functions import round as spark_round

# Initialize Spark session
spark = SparkSession.builder \
    .appName("load-facts") \
    .config("spark.executor.memory", "4g") \
    .config("spark.executor.cores", "2") \
    .config("spark.shuffle.partitions", "200") \
    .getOrCreate()

spark.sparkContext.setLogLevel("INFO")

# Database connection properties
db_properties = {
    "user": "postgres",
    "password": "password",
    "driver": "org.postgresql.Driver"
}

db_url = "jdbc:postgresql://localhost:5432/analytics_warehouse"


def load_orders_fact(spark):
    """Load orders fact table"""
    print("Loading orders fact table...")

    # Read staging data
    orders = spark.read \
        .jdbc(db_url, "staging.stg_orders", db_properties)

    # Convert order_date to date_id format
    orders = orders.withColumn(
        "order_date_id",
        spark_round(
            col("order_date").cast("date").cast("string").regexp_replace("-", "").cast("int")
        )
    )

    # Calculate derived metrics
    orders = orders.withColumn(
        "gross_profit",
        col("order_amount") - col("cost_amount")
    ).withColumn(
        "gross_margin_pct",
        spark_round((col("gross_profit") / col("order_amount")) * 100, 2)
    ).withColumn(
        "dw_created_at",
        current_timestamp()
    ).withColumn(
        "dw_updated_at",
        current_timestamp()
    )

    # Select required columns
    fact_columns = [
        "order_id", "order_date_id", "customer_id", "product_id",
        "supplier_id", "quantity", "list_price", "discount_amount",
        "order_amount", "tax_amount", "shipping_amount", "total_amount",
        "cost_amount", "gross_profit", "gross_margin_pct",
        "order_status", "payment_status", "shipping_status",
        "created_at", "dw_created_at", "dw_updated_at"
    ]

    orders = orders.select(*fact_columns)

    orders.write \
        .mode("append") \
        .jdbc(db_url, "public.fact_orders", db_properties)

    print(f"✓ Loaded {orders.count()} orders")


def load_deliveries_fact(spark):
    """Load deliveries fact table"""
    print("Loading deliveries fact table...")

    # Read staging data
    deliveries = spark.read \
        .jdbc(db_url, "staging.stg_deliveries", db_properties)

    # Convert dates to date_id format
    deliveries = deliveries.withColumn(
        "order_date_id",
        spark_round(
            col("order_date").cast("date").cast("string").regexp_replace("-", "").cast("int")
        )
    ).withColumn(
        "delivery_date_id",
        spark_round(
            col("delivery_date").cast("date").cast("string").regexp_replace("-", "").cast("int")
        )
    ).withColumn(
        "promised_date_id",
        spark_round(
            col("promised_date").cast("date").cast("string").regexp_replace("-", "").cast("int")
        )
    )

    # Calculate lead time
    deliveries = deliveries.withColumn(
        "lead_time_days",
        (col("delivery_date").cast("date") - col("order_date").cast("date"))
    ).withColumn(
        "is_on_time",
        col("delivery_date") <= col("promised_date")
    ).withColumn(
        "dw_created_at",
        current_timestamp()
    ).withColumn(
        "dw_updated_at",
        current_timestamp()
    )

    # Select required columns
    fact_columns = [
        "delivery_id", "po_id", "supplier_id", "product_id",
        "order_date_id", "delivery_date_id", "promised_date_id",
        "quantity_ordered", "quantity_delivered", "quantity_rejected",
        "unit_cost", "total_cost", "lead_time_days",
        "is_on_time", "is_quality_pass", "delivery_status",
        "created_at", "dw_created_at", "dw_updated_at"
    ]

    deliveries = deliveries.select(*fact_columns)

    deliveries.write \
        .mode("append") \
        .jdbc(db_url, "public.fact_deliveries", db_properties)

    print(f"✓ Loaded {deliveries.count()} deliveries")


def load_transactions_fact(spark):
    """Load transactions fact table"""
    print("Loading transactions fact table...")

    # Read staging data
    transactions = spark.read \
        .jdbc(db_url, "staging.stg_transactions", db_properties)

    # Convert transaction_date to date_id
    transactions = transactions.withColumn(
        "transaction_date_id",
        spark_round(
            col("transaction_date").cast("date").cast("string").regexp_replace("-", "").cast("int")
        )
    ).withColumn(
        "net_amount",
        col("debit_amount") - col("credit_amount")
    ).withColumn(
        "dw_created_at",
        current_timestamp()
    ).withColumn(
        "dw_updated_at",
        current_timestamp()
    )

    # Select required columns
    fact_columns = [
        "transaction_id", "transaction_date_id", "gl_account_id",
        "debit_amount", "credit_amount", "net_amount",
        "transaction_type", "description", "reference_id",
        "currency_code", "exchange_rate",
        "is_intercompany", "is_reconciled",
        "created_at", "dw_created_at", "dw_updated_at"
    ]

    transactions = transactions.select(*fact_columns)

    transactions.write \
        .mode("append") \
        .jdbc(db_url, "public.fact_transactions", db_properties)

    print(f"✓ Loaded {transactions.count()} transactions")


def load_budget_actuals_fact(spark):
    """Load budget vs actuals fact table"""
    print("Loading budget vs actuals fact table...")

    # Read budgets and actuals
    budgets = spark.read \
        .jdbc(db_url, "staging.stg_budgets", db_properties)

    actuals = spark.read \
        .jdbc(db_url, "staging.stg_actuals", db_properties)

    # Join budgets and actuals
    budgets = budgets.withColumn(
        "date_id",
        spark_round(
            col("budget_date").cast("date").cast("string").regexp_replace("-", "").cast("int")
        )
    )

    actuals = actuals.withColumn(
        "date_id",
        spark_round(
            col("actual_date").cast("date").cast("string").regexp_replace("-", "").cast("int")
        )
    )

    budget_actuals = budgets.join(
        actuals,
        on=["gl_account_id", "date_id"],
        how="full"
    ).withColumn(
        "variance_amount",
        col("actual_amount") - col("budget_amount")
    ).withColumn(
        "variance_pct",
        spark_round((col("variance_amount") / col("budget_amount")) * 100, 2)
    ).withColumn(
        "dw_created_at",
        current_timestamp()
    ).withColumn(
        "dw_updated_at",
        current_timestamp()
    )

    budget_actuals.write \
        .mode("append") \
        .jdbc(db_url, "public.fact_budget_actuals", db_properties)

    print(f"✓ Loaded {budget_actuals.count()} budget vs actuals records")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python load_facts.py <fact_name>")
        print("Available facts: orders, deliveries, transactions, budget_actuals")
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
            print(f"Unknown fact: {fact}")
            sys.exit(1)

        print(f"\n✓ Successfully loaded {fact} fact table")

    except Exception as e:
        print(f"✗ Error loading {fact}: {str(e)}")
        sys.exit(1)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
