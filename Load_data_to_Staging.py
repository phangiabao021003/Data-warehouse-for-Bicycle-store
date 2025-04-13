import pyarrow
import pyodbc as odbc
from sqlserver import SQLServer
import pandas as pd
from google.cloud import bigquery
import os
from datetime import datetime
from google.cloud.exceptions import NotFound

project_id = 'bicycle-store-data-warehouse'
dataset_id = 'Data'
sql_server_instance = SQLServer(server_name="host.docker.internal", database_name='Bicycle_store_dwh', username='sa', password='airflow')
connection = sql_server_instance.connect_to_sql_server()
# Kết nối BigQuery
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"/opt/airflow/dags/bicycle-store-data-warehouse-3d11f1b48a0b.json"
client = bigquery.Client()
# driver = 'ODBC Driver 17 for SQL Server'
# connection_string = f"mssql+pyodbc://{SERVER_NAME}/{DATABASE_NAME}?driver={driver}"
# Initialize BigQuery client

try:
    cursor = sql_server_instance.cursor()
    cursor.execute("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
    tables = [f"{row.TABLE_SCHEMA}.{row.TABLE_NAME}" for row in cursor.fetchall()]

    # Xử lý từng bảng
    for table_name in tables:
        print(f"Loading table: {table_name}")

        # Fetch dữ liệu vào DataFrame
        df = pd.read_sql(f"SELECT * FROM {table_name}", connection)

        # Tải trực tiếp lên BigQuery từ DataFrame
        table_id = f"{project_id}.{dataset_id}.{table_name.replace('.', '_')}"
        job_config = bigquery.LoadJobConfig(
            autodetect=True,
            write_disposition="WRITE_TRUNCATE"  # Thay thế bảng hiện tại
        )

        # Tải DataFrame lên BigQuery
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)

        # Chờ đợi cho job hoàn tất
        job.result()
        print(f"Loaded {job.output_rows} rows to {table_id}")

except Exception as e:
    print(f"An error occurred: {e}")

# try:
#     # Check existence of dataset on BigQuery
#     dataset = client.get_dataset(dataset_id)  
# except NotFound:
#     # Nếu dataset không tồn tại, tạo mới
#     dataset = bigquery.Dataset(dataset_id)
#     dataset.location = ""  
#     dataset = client.create_dataset(dataset)  # Tạo dataset
# try:
#         subfolder_name = "data"
#         subfolder_path = os.path.join("/opt/airflow/dags/data", subfolder_name)
#         os.makedirs(subfolder_path, exist_ok=True)
#         cursor = sql_server_instance.cursor()
#         cursor.execute("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
#         tables = [f"{row.TABLE_SCHEMA}.{row.TABLE_NAME}" for row in cursor.fetchall()]

#         # Process each table
#         for table_name in tables:
#             print(f"Loading table: {table_name}")

#             # Fetch data into DataFrame
#             df = pd.read_sql(f"SELECT * FROM {table_name}", connection)

#             # Save DataFrame to CSV
#             csv_file_path = os.path.join(subfolder_path, f"{table_name}.csv")
#             df.to_csv(csv_file_path, index=False)
#             # Set destination table ID
#             table_id = f"{project_id}.{dataset_id}.{table_name.replace('.', '_')}"

#             # Define BigQuery load job config
#             job_config = bigquery.LoadJobConfig(
#                 source_format=bigquery.SourceFormat.CSV,
#                 skip_leading_rows=1,
#                 autodetect=True,
#                 write_disposition="WRITE_TRUNCATE"  # Replace existing table
#             )

#             # Load CSV into BigQuery
#             with open(csv_file_path, "rb") as source_file:
#                 job = client.load_table_from_file(source_file, table_id, job_config=job_config)

#             # Wait for the load job to complete
#             job.result()
#             print(f"Loaded {job.output_rows} rows to {table_id}")

# except Exception as e:
#     print(f"An error occurred: {e}")