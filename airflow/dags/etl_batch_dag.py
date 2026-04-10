"""
Airflow DAG for Batch ETL Processing
Daily aggregation and dimensional modeling of data
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable

import logging

logger = logging.getLogger(__name__)

# Default arguments
default_args = {
    'owner': 'analytics-team',
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email': ['analytics-alerts@company.com']
}

# DAG definition
dag = DAG(
    'etl_batch_processing',
    default_args=default_args,
    description='Daily batch ETL: data loading, transformation, aggregation',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    catchup=False,
    tags=['etl', 'batch-processing']
)


def load_etl_audit():
    """Log ETL start"""
    from sqlalchemy import create_engine, text
    from datetime import datetime

    db_url = Variable.get("DB_URL")
    engine = create_engine(db_url)

    with engine.connect() as conn:
        conn.execute(
            text("""
            INSERT INTO public.dw_load_audit
            (process_name, source_system, table_name, status, start_time)
            VALUES (:process, :source, :table, :status, :start_time)
            """),
            {
                'process': 'etl_batch_processing',
                'source': 'kafka_staging',
                'table': 'all_tables',
                'status': 'IN_PROGRESS',
                'start_time': datetime.utcnow()
            }
        )
        conn.commit()


# Spark job paths
SPARK_JOBS_PATH = "/opt/airflow/spark_jobs"

with dag:
    # Start task
    etl_start = BashOperator(
        task_id='etl_start',
        bash_command='echo "Starting ETL batch processing at $(date)"'
    )

    # Data loading from staging
    with TaskGroup('load_dimensional_data') as load_dims:
        load_products = SparkSubmitOperator(
            task_id='load_products_dimension',
            application=f'{SPARK_JOBS_PATH}/load_dimensions.py',
            application_args=['products'],
            spark_master='spark://localhost:7077',
            conf={
                'spark.executor.memory': '4g',
                'spark.executor.cores': '2',
                'spark.shuffle.partitions': '200'
            }
        )

        load_customers = SparkSubmitOperator(
            task_id='load_customers_dimension',
            application=f'{SPARK_JOBS_PATH}/load_dimensions.py',
            application_args=['customers'],
            spark_master='spark://localhost:7077'
        )

        load_suppliers = SparkSubmitOperator(
            task_id='load_suppliers_dimension',
            application=f'{SPARK_JOBS_PATH}/load_dimensions.py',
            application_args=['suppliers'],
            spark_master='spark://localhost:7077'
        )

        load_gl_accounts = SparkSubmitOperator(
            task_id='load_gl_accounts_dimension',
            application=f'{SPARK_JOBS_PATH}/load_dimensions.py',
            application_args=['gl_accounts'],
            spark_master='spark://localhost:7077'
        )

    # Load fact tables
    with TaskGroup('load_fact_tables') as load_facts:
        load_orders = SparkSubmitOperator(
            task_id='load_orders_fact',
            application=f'{SPARK_JOBS_PATH}/load_facts.py',
            application_args=['orders'],
            spark_master='spark://localhost:7077'
        )

        load_deliveries = SparkSubmitOperator(
            task_id='load_deliveries_fact',
            application=f'{SPARK_JOBS_PATH}/load_facts.py',
            application_args=['deliveries'],
            spark_master='spark://localhost:7077'
        )

        load_transactions = SparkSubmitOperator(
            task_id='load_transactions_fact',
            application=f'{SPARK_JOBS_PATH}/load_facts.py',
            application_args=['transactions'],
            spark_master='spark://localhost:7077'
        )

    # Calculate daily KPI metrics
    with TaskGroup('calculate_kpi_metrics') as calc_kpis:
        calc_ecommerce_kpi = SparkSubmitOperator(
            task_id='calc_ecommerce_kpi',
            application=f'{SPARK_JOBS_PATH}/calculate_kpis.py',
            application_args=['ecommerce'],
            spark_master='spark://localhost:7077'
        )

        calc_supply_chain_kpi = SparkSubmitOperator(
            task_id='calc_supply_chain_kpi',
            application=f'{SPARK_JOBS_PATH}/calculate_kpis.py',
            application_args=['supply_chain'],
            spark_master='spark://localhost:7077'
        )

        calc_financial_kpi = SparkSubmitOperator(
            task_id='calc_financial_kpi',
            application=f'{SPARK_JOBS_PATH}/calculate_kpis.py',
            application_args=['financial'],
            spark_master='spark://localhost:7077'
        )

        calc_unified_kpi = SparkSubmitOperator(
            task_id='calc_unified_kpi',
            application=f'{SPARK_JOBS_PATH}/calculate_kpis.py',
            application_args=['unified'],
            spark_master='spark://localhost:7077'
        )

    # Data quality checks on warehouse
    refresh_analytics_views = PostgresOperator(
        task_id='refresh_analytics_views',
        sql=[
            'REFRESH MATERIALIZED VIEW analytics.ecommerce_daily_metrics;',
            'REFRESH MATERIALIZED VIEW analytics.supply_chain_daily_metrics;',
            'REFRESH MATERIALIZED VIEW analytics.financial_daily_metrics;',
            'REFRESH MATERIALIZED VIEW analytics.unified_kpi_metrics;'
        ],
        postgres_conn_id='analytics_warehouse'
    )

    # Mark processed records
    mark_processed = BashOperator(
        task_id='mark_processed_records',
        bash_command="""
        psql -h ${DB_HOST} -U ${DB_USER} -d analytics_warehouse << EOF
        UPDATE staging.stg_orders SET processed = TRUE WHERE processed = FALSE;
        UPDATE staging.stg_deliveries SET processed = TRUE WHERE processed = FALSE;
        UPDATE staging.stg_transactions SET processed = TRUE WHERE processed = FALSE;
        EOF
        """
    )

    # End task
    etl_end = BashOperator(
        task_id='etl_end',
        bash_command='echo "ETL batch processing completed at $(date)"'
    )

    # Task dependencies
    etl_start >> load_dims >> load_facts >> calc_kpis >> refresh_analytics_views >> mark_processed >> etl_end
