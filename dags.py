from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from datetime import datetime, timedelta
from google.cloud import bigquery
import os
import subprocess
import pandas as pd

# Set the Google Cloud credentials environment variable
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"/opt/airflow/dags/bicycle-store-data-warehouse-3d11f1b48a0b.json"

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,               # Each task instance runs independently of the previous instances
    'email_on_failure': False,              # Disable email notifications on task failure
    'email_on_retry': False,                # Disable email notifications on retries
    'retries': 0,                           # No retry after a task fails
}

# Define the DAG
dag = DAG(
    'Quarterly_Workflow',
    default_args=default_args,
    schedule_interval='0 0 1 1,4,7,10 *',  # Run every 3 months (Jan, Apr, Jul, Oct)
    start_date=datetime(2024, 2, 5),       # Set your start date
    catchup=False,                         # Do not run for previous missed periods
)
# Function to read Python file
def run_python_file(file_path):
    with open(file_path, 'r') as file:
        script_content = file.read()  # Đọc nội dung tệp Python
    
    try:
        exec(script_content)  # Thực thi mã trong tệp Python
    except Exception as e:
        print(f"Error executing the script: {e}")

# Function to read SQL files
def read_sql_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# Function to execute a BigQuery file
def execute_query(file_path):
    client = bigquery.Client()
    sql_query = read_sql_file(file_path)
    query_job = client.query(sql_query)
    query_job.result()
    print(f"Query from {file_path} executed successfully.")


t1 = PythonOperator(
    task_id='Load_data_to_Stagging',
    python_callable =run_python_file,
    op_args=["/opt/airflow/dags/Load_data_to_Staging.py"], 
    dag=dag, )
t2 = PythonOperator(
    task_id='Create_dim_tables',
    python_callable=execute_query,
    op_args=["/opt/airflow/dags/Create_dim.sql"],
    dag=dag,
)
t3=PythonOperator(
    task_id='Create_fact_tables',
    python_callable=execute_query,
    op_args=["/opt/airflow/dags/Create_fact.sql"],
    dag=dag,
)
t4=PythonOperator(
    task_id='Export_data_to_Excel_file',
    python_callable=run_python_file,
    op_args=["/opt/airflow/dags/Export_data_to_Excel.py"]
)

t1>>t2>>t3>>t4