-- Create Airflow metadata database
-- This script runs during postgres initialization
SELECT 'CREATE DATABASE airflow_metadata'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow_metadata')\gexec
