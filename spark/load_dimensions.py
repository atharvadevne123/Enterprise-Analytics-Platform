"""
PySpark Job: Load Dimension Tables
Loads and updates dimension tables from staging data
"""

import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, coalesce, lit
from datetime import datetime

# Initialize Spark session
spark = SparkSession.builder \
    .appName("load-dimensions") \
    .config("spark.executor.memory", "4g") \
    .config("spark.executor.cores", "2") \
    .config("spark.shuffle.partitions", "200") \
    .getOrCreate()

spark.sparkContext.setLogLevel("INFO")

# Database connection properties
db_properties = {
    "user": "postgres",
    "password": "password",  # Use environment variable in production
    "driver": "org.postgresql.Driver"
}

db_url = "jdbc:postgresql://localhost:5432/analytics_warehouse"


def load_products_dimension(spark):
    """Load products dimension table"""
    print("Loading products dimension...")

    # Read from staging or source system
    df = spark.read \
        .jdbc(db_url, "staging.stg_products", db_properties)

    # Add data warehouse metadata columns
    df = df.withColumn("dw_created_at", current_timestamp()) \
        .withColumn("dw_updated_at", current_timestamp())

    # Write to dimension table (SCD Type 2: Keep history)
    df.write \
        .mode("overwrite") \
        .jdbc(db_url, "public.dim_products", db_properties)

    print(f"✓ Loaded {df.count()} products")


def load_customers_dimension(spark):
    """Load customers dimension table"""
    print("Loading customers dimension...")

    df = spark.read \
        .jdbc(db_url, "staging.stg_customers", db_properties)

    # Calculate lifetime value from orders
    orders_df = spark.read \
        .jdbc(db_url, "staging.stg_orders", db_properties)

    ltv_df = orders_df.groupBy("customer_id") \
        .agg({"total_amount": "sum"}) \
        .withColumnRenamed("sum(total_amount)", "lifetime_value")

    df = df.join(ltv_df, on="customer_id", how="left") \
        .withColumn("lifetime_value", coalesce(col("lifetime_value"), lit(0))) \
        .withColumn("dw_created_at", current_timestamp()) \
        .withColumn("dw_updated_at", current_timestamp())

    df.write \
        .mode("overwrite") \
        .jdbc(db_url, "public.dim_customers", db_properties)

    print(f"✓ Loaded {df.count()} customers")


def load_suppliers_dimension(spark):
    """Load suppliers dimension table"""
    print("Loading suppliers dimension...")

    df = spark.read \
        .jdbc(db_url, "staging.stg_suppliers", db_properties)

    # Calculate supplier metrics from deliveries
    deliveries_df = spark.read \
        .jdbc(db_url, "staging.stg_deliveries", db_properties)

    metrics_df = deliveries_df.groupBy("supplier_id") \
        .agg({
            "is_on_time": "avg",  # on-time delivery %
            "is_quality_pass": "avg"  # quality score
        }) \
        .withColumnRenamed("avg(is_on_time)", "on_time_delivery_pct") \
        .withColumnRenamed("avg(is_quality_pass)", "quality_score")

    df = df.join(metrics_df, on="supplier_id", how="left") \
        .withColumn("dw_created_at", current_timestamp()) \
        .withColumn("dw_updated_at", current_timestamp())

    df.write \
        .mode("overwrite") \
        .jdbc(db_url, "public.dim_suppliers", db_properties)

    print(f"✓ Loaded {df.count()} suppliers")


def load_gl_accounts_dimension(spark):
    """Load GL accounts dimension table"""
    print("Loading GL accounts dimension...")

    df = spark.read \
        .jdbc(db_url, "staging.stg_gl_accounts", db_properties)

    df = df.withColumn("dw_created_at", current_timestamp())

    df.write \
        .mode("overwrite") \
        .jdbc(db_url, "public.dim_gl_accounts", db_properties)

    print(f"✓ Loaded {df.count()} GL accounts")


def load_date_dimension(spark):
    """Load date dimension table (run once)"""
    print("Loading date dimension...")

    from datetime import datetime, timedelta

    # Generate dates for 10 years
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2030, 12, 31)

    dates = []
    current = start_date

    while current <= end_date:
        dates.append({
            'date_id': int(current.strftime('%Y%m%d')),
            'date': current.date(),
            'year': current.year,
            'quarter': (current.month - 1) // 3 + 1,
            'month': current.month,
            'week': current.isocalendar()[1],
            'day_of_month': current.day,
            'day_of_week': current.weekday() + 1,
            'day_name': current.strftime('%A'),
            'month_name': current.strftime('%B'),
            'is_weekend': 1 if current.weekday() >= 5 else 0,
            'is_holiday': 0
        })
        current += timedelta(days=1)

    df = spark.createDataFrame(dates)

    df.write \
        .mode("overwrite") \
        .jdbc(db_url, "public.dim_dates", db_properties)

    print(f"✓ Loaded {df.count()} dates")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python load_dimensions.py <dimension_name>")
        print("Available dimensions: products, customers, suppliers, gl_accounts, dates")
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
            print(f"Unknown dimension: {dimension}")
            sys.exit(1)

        print(f"\n✓ Successfully loaded {dimension} dimension")

    except Exception as e:
        print(f"✗ Error loading {dimension}: {str(e)}")
        sys.exit(1)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
