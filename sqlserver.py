import pyodbc as odbc
import logging

class SQLServer:
    DRIVER_NAME = 'ODBC Driver 17 for SQL Server'

    def __init__(self, server_name="host.docker.internal", database_name=None, username=None, password=None):

        self.server_name = server_name
        self.database_name = database_name
        self.username = username
        self.password = password
        self.conn = None  # Đảm bảo khởi tạo conn

    def _connection_string(self):
        """
        Xây dựng chuỗi kết nối đến SQL Server, có thể sử dụng SQL Server Authentication hoặc Windows Authentication.
        """
        if self.username and self.password:
            # Sử dụng SQL Server Authentication
            conn_string = f"""
                DRIVER={{{self.DRIVER_NAME}}};
                SERVER={self.server_name};
                DATABASE={self.database_name};
                UID={self.username};
                PWD={self.password};
                Timeout=90;
            """
        else:
            # Sử dụng Windows Authentication
            conn_string = f"""
                DRIVER={{{self.DRIVER_NAME}}};
                SERVER={self.server_name};
                DATABASE={self.database_name};
                Trust_Connection=yes;
                Timeout=90;
            """
        return conn_string

    def connect_to_sql_server(self):
        """
        Kết nối đến SQL Server và trả về đối tượng kết nối.
        """
        try:
            self.conn = odbc.connect(self._connection_string())
            logging.info('Connected to SQL Server successfully')
            return self.conn
        except Exception as e:
            logging.error('Failed to connect to SQL Server', exc_info=True)
            self.conn = None
            return None

    def query(self, sql_statement):
        """
        Thực hiện câu lệnh SQL và trả về kết quả.
        
        :param sql_statement: Câu lệnh SQL cần thực hiện
        :return: (columns, data) nếu truy vấn thành công, None nếu có lỗi
        """
        if self.conn is None:
            logging.warning('No active connection')
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_statement)
            data = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return columns, data
        except Exception as e:
            logging.error('Failed to execute query', exc_info=True)
            return None

    def cursor(self):
        """
        Trả về đối tượng cursor nếu có kết nối.
        """
        if not self.check_connection():
            logging.warning('No active connection')
            return None
        return self.conn.cursor()

    def check_connection(self):
        """
        Kiểm tra trạng thái kết nối.
        
        :return: True nếu có kết nối, False nếu không
        """
        return self.conn is not None

    def close_connection(self):
        """
        Đóng kết nối SQL Server nếu đang mở.
        """
        if self.conn:
            try:
                self.conn.close()
                logging.info('Connection closed successfully')
            except Exception as e:
                logging.error('Failed to close connection', exc_info=True)
            finally:
                self.conn = None

