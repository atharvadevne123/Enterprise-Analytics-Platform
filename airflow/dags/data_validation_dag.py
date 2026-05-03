"""
Airflow DAG for Data Validation and Quality Checks
Runs daily to validate incoming data before ETL processing
"""

import logging
from datetime import datetime, timedelta

from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

from airflow import DAG

logger = logging.getLogger(__name__)

# Default arguments
default_args = {
    'owner': 'analytics-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email': ['analytics-alerts@company.com']
}

# DAG definition
dag = DAG(
    'data_validation',
    default_args=default_args,
    description='Data validation and quality checks',
    schedule_interval='0 0 * * *',  # Daily at midnight
    catchup=False,
    tags=['data-quality', 'validation']
)


def validate_orders_table():
    """Validate orders data quality"""
    import pandas as pd
    from sqlalchemy import create_engine

    db_url = Variable.get("DB_URL")
    engine = create_engine(db_url)

    # Check for null values in critical columns
    with engine.connect() as conn:
        df = pd.read_sql_query(
            """
            SELECT COUNT(*) as total_records,
                   SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) as null_order_id,
                   SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) as null_customer_id,
                   SUM(CASE WHEN total_amount < 0 THEN 1 ELSE 0 END) as negative_amounts
            FROM staging.stg_orders
            WHERE processed = FALSE
            """,
            conn
        )

    total = df['total_records'].iloc[0]
    nulls = df['null_order_id'].iloc[0] + df['null_customer_id'].iloc[0]
    negatives = df['negative_amounts'].iloc[0]

    logger.info(f"Orders validation: Total={total}, Nulls={nulls}, Negatives={negatives}")

    if nulls > 0 or negatives > 0:
        raise ValueError(f"Data quality check failed: Nulls={nulls}, Negatives={negatives}")


def validate_deliveries_table():
    """Validate deliveries data quality"""
    import pandas as pd
    from sqlalchemy import create_engine

    db_url = Variable.get("DB_URL")
    engine = create_engine(db_url)

    with engine.connect() as conn:
        df = pd.read_sql_query(
            """
            SELECT COUNT(*) as total_records,
                   SUM(CASE WHEN quantity_delivered > quantity_ordered THEN 1 ELSE 0 END) as over_deliveries
            FROM staging.stg_deliveries
            WHERE processed = FALSE
            """,
            conn
        )

    total = df['total_records'].iloc[0]
    over_deliveries = df['over_deliveries'].iloc[0]

    logger.info(f"Deliveries validation: Total={total}, Over-deliveries={over_deliveries}")

    if over_deliveries > 0:
        raise ValueError(f"Delivery validation failed: Over-deliveries={over_deliveries}")


def validate_transactions_table():
    """Validate financial transactions data quality"""
    import pandas as pd
    from sqlalchemy import create_engine

    db_url = Variable.get("DB_URL")
    engine = create_engine(db_url)

    with engine.connect() as conn:
        df = pd.read_sql_query(
            """
            SELECT COUNT(*) as total_records,
                   SUM(CASE WHEN (debit + credit) = 0 THEN 1 ELSE 0 END) as zero_amounts
            FROM staging.stg_transactions
            WHERE processed = FALSE
            """,
            conn
        )

    total = df['total_records'].iloc[0]
    zero_amounts = df['zero_amounts'].iloc[0]

    logger.info(f"Transactions validation: Total={total}, Zero-amounts={zero_amounts}")

    if zero_amounts > 0:
        raise ValueError(f"Transaction validation failed: Zero-amounts={zero_amounts}")


def record_validation_status(status: str, details: str):
    """Record validation status in database"""
    from datetime import datetime

    from sqlalchemy import create_engine, text

    db_url = Variable.get("DB_URL")
    engine = create_engine(db_url)

    with engine.connect() as conn:
        conn.execute(
            text("""
            INSERT INTO public.data_quality_log
            (check_name, status, record_count, run_timestamp)
            VALUES (:check_name, :status, :record_count, :timestamp)
            """),
            {
                'check_name': 'daily_validation',
                'status': status,
                'record_count': 0,
                'timestamp': datetime.utcnow()
            }
        )
        conn.commit()


# Task definitions

with dag:
    # Start task
    validate_start = BashOperator(
        task_id='validate_start',
        bash_command='echo "Starting data validation at $(date)"'
    )

    # Validation tasks in parallel
    with TaskGroup('validate_staging_tables') as validate_tables:
        validate_orders = PythonOperator(
            task_id='validate_orders',
            python_callable=validate_orders_table
        )

        validate_deliveries = PythonOperator(
            task_id='validate_deliveries',
            python_callable=validate_deliveries_table
        )

        validate_transactions = PythonOperator(
            task_id='validate_transactions',
            python_callable=validate_transactions_table
        )

    # Create validation summary
    validation_summary = BashOperator(
        task_id='validation_summary',
        bash_command='echo "All validations completed successfully"'
    )

    # Record validation status
    record_status = PythonOperator(
        task_id='record_validation_status',
        python_callable=record_validation_status,
        op_kwargs={'status': 'PASSED', 'details': 'All checks passed'}
    )

    # Task dependencies
    validate_start >> validate_tables >> validation_summary >> record_status
