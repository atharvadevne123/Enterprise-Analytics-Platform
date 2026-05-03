"""
PySpark Job: Calculate Daily KPI Metrics
Computes aggregated metrics for all domains
"""

import sys

from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, count, current_timestamp
from pyspark.sql.functions import round as spark_round
from pyspark.sql.functions import sum as spark_sum

# Initialize Spark session
spark = SparkSession.builder \
    .appName("calculate-kpis") \
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


def calculate_ecommerce_kpis(spark):
    """Calculate e-commerce daily KPIs"""
    print("Calculating e-commerce KPIs...")

    # Read fact and dimension tables
    orders = spark.read \
        .jdbc(db_url, "public.fact_orders", db_properties)

    # Group by order_date_id and calculate metrics
    metrics = orders.groupBy("order_date_id").agg(
        count("order_id").alias("total_orders"),
        count("customer_id").alias("total_customers"),
        spark_sum("total_amount").alias("total_revenue"),
        spark_sum("cost_amount").alias("total_cost"),
        spark_sum("gross_profit").alias("gross_profit"),
        spark_round(avg("total_amount"), 2).alias("average_order_value"),
    ).withColumn(
        "dw_updated_at",
        current_timestamp()
    )

    metrics.write \
        .mode("append") \
        .jdbc(db_url, "analytics.ecommerce_daily_metrics", db_properties)

    print(f"✓ Calculated e-commerce KPIs for {metrics.count()} days")


def calculate_supply_chain_kpis(spark):
    """Calculate supply chain daily KPIs"""
    print("Calculating supply chain KPIs...")

    # Read deliveries fact
    deliveries = spark.read \
        .jdbc(db_url, "public.fact_deliveries", db_properties)

    # Calculate metrics by delivery_date_id
    metrics = deliveries.groupBy("delivery_date_id").agg(
        count("delivery_id").alias("total_deliveries"),
        spark_sum("is_on_time").alias("on_time_deliveries"),
        spark_round(avg("is_on_time") * 100, 2).alias("on_time_delivery_pct"),
        spark_round(spark_sum("total_cost"), 2).alias("total_procurement_cost"),
        spark_round(avg("lead_time_days"), 2).alias("average_lead_time_days"),
        spark_round(avg("is_quality_pass") * 100, 2).alias("supplier_quality_score"),
    ).withColumnRenamed(
        "delivery_date_id",
        "date_id"
    ).withColumn(
        "dw_updated_at",
        current_timestamp()
    )

    metrics.write \
        .mode("append") \
        .jdbc(db_url, "analytics.supply_chain_daily_metrics", db_properties)

    print(f"✓ Calculated supply chain KPIs for {metrics.count()} days")


def calculate_financial_kpis(spark):
    """Calculate financial daily KPIs"""
    print("Calculating financial KPIs...")

    # Read transactions and budgets
    transactions = spark.read \
        .jdbc(db_url, "public.fact_transactions", db_properties)

    # Calculate daily financials
    metrics = transactions.groupBy("transaction_date_id").agg(
        spark_round(spark_sum(
            col("debit_amount")
        ), 2).alias("total_revenue"),
        spark_round(spark_sum(
            col("credit_amount")
        ), 2).alias("total_expense"),
    ).withColumnRenamed(
        "transaction_date_id",
        "date_id"
    ).withColumn(
        "net_income",
        col("total_revenue") - col("total_expense")
    ).withColumn(
        "dw_updated_at",
        current_timestamp()
    )

    metrics.write \
        .mode("append") \
        .jdbc(db_url, "analytics.financial_daily_metrics", db_properties)

    print(f"✓ Calculated financial KPIs for {metrics.count()} days")


def calculate_unified_kpis(spark):
    """Calculate unified cross-domain KPIs"""
    print("Calculating unified KPIs...")

    # Read all relevant data
    deliveries = spark.read.jdbc(db_url, "public.fact_deliveries", db_properties)

    # Order-to-cash cycle (simple: average delivery days)
    order_cash_cycle = deliveries.groupBy("order_date_id").agg(
        spark_round(avg("lead_time_days"), 0).alias("order_to_cash_cycle_days")
    )

    # Merge all metrics
    metrics = order_cash_cycle.withColumnRenamed(
        "order_date_id",
        "date_id"
    ).withColumn(
        "revenue_per_supplier",
        spark_round(spark_sum("revenue").over(), 2)
    ).withColumn(
        "profit_per_product",
        spark_round(spark_sum("profit").over(), 2)
    ).withColumn(
        "inventory_to_sales_ratio",
        0.0  # Would calculate from inventory and sales data
    ).withColumn(
        "cash_conversion_cycle_days",
        col("order_to_cash_cycle_days")
    ).withColumn(
        "dw_updated_at",
        current_timestamp()
    ).select(
        "date_id", "revenue_per_supplier", "profit_per_product",
        "order_to_cash_cycle_days", "inventory_to_sales_ratio",
        "cash_conversion_cycle_days", "dw_updated_at"
    )

    metrics.write \
        .mode("append") \
        .jdbc(db_url, "analytics.unified_kpi_metrics", db_properties)

    print(f"✓ Calculated unified KPIs for {metrics.count()} days")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python calculate_kpis.py <domain>")
        print("Available domains: ecommerce, supply_chain, financial, unified")
        sys.exit(1)

    domain = sys.argv[1]

    try:
        if domain == "ecommerce":
            calculate_ecommerce_kpis(spark)
        elif domain == "supply_chain":
            calculate_supply_chain_kpis(spark)
        elif domain == "financial":
            calculate_financial_kpis(spark)
        elif domain == "unified":
            calculate_unified_kpis(spark)
        else:
            print(f"Unknown domain: {domain}")
            sys.exit(1)

        print(f"\n✓ Successfully calculated {domain} KPIs")

    except Exception as e:
        print(f"✗ Error calculating KPIs: {str(e)}")
        sys.exit(1)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
