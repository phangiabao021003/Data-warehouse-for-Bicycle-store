from google.cloud import bigquery
import pandas as pd
import openpyxl
import os
# Đặt biến môi trường cho Google Cloud Credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"/opt/airflow/dags/bicycle-store-data-warehouse-3d11f1b48a0b.json"

# Khởi tạo client BigQuery
client = bigquery.Client()

# Các thông số kết nối
BIGQUERY_PROJECT_ID = 'bicycle-store-data-warehouse'
BIGQUERY_DATASET_ID = 'OLAP'

# Tạo URI (chuỗi) để chỉ định dataset
dataset_ref = client.dataset(BIGQUERY_DATASET_ID)
tables = client.list_tables(dataset_ref)

# Duyệt qua từng bảng và tải dữ liệu về dưới dạng Excel
for table in tables:
    table_name = table.table_id

    # Truy vấn dữ liệu từ bảng BigQuery
    query = f"SELECT * FROM `{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET_ID}.{table_name}`"
    
    # Thực hiện truy vấn và lấy dữ liệu qua BigQuery Storage API
    query_job = client.query(query)
    result = query_job.result().to_dataframe()

    # Tạo đường dẫn file csv
    output_directory = r"/opt/airflow/dags/transformed data"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    file_path = os.path.join(output_directory, f"{table_name}.csv")
    
    # Lưu DataFrame vào tệp CSV
    result.to_csv(file_path, index=False)
    print(f"Đã tải dữ liệu từ bảng {table_name} và lưu vào {file_path}")


folder_path = "/opt/airflow/dags/transformed data"  

# Tạo một file Excel mới
with pd.ExcelWriter('/opt/airflow/dags/Excel_file/Combined_data.xlsx', engine='openpyxl') as writer:
    # Lặp qua tất cả các file CSV trong thư mục
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):  # Kiểm tra nếu là file CSV
            # Đọc file CSV
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)
            
            # Lấy tên sheet từ tên file (loại bỏ phần mở rộng .csv)
            sheet_name = os.path.splitext(filename)[0]
            
            # Ghi dữ liệu vào sheet tương ứng trong Excel
            df.to_excel(writer, sheet_name=sheet_name, index=False)
