import pymssql
import os
from dotenv import load_dotenv
import time

class DatabaseConnection:
    def __init__(self):
        load_dotenv()  # Load environment variables from .env file
        self.server =  os.getenv('db_server')
        self.database = os.getenv('db_database')
        self.username = os.getenv('db_username')
        self.password = os.getenv('db_password')  # Ensure the variable name matches the .env file
        self.conn = None
        self.max_retries = 3  # Maximum number of retries
        self.retry_delay = 5  # Delay between retries in seconds
    def connect(self):
        attempt = 0
        while attempt < self.max_retries:
            try:
                self.conn = pymssql.connect(
                    server=self.server,
                    user=self.username,
                    password=self.password,
                    database=self.database,
                    timeout=5  # Set a timeout for the connection
                )
                print("Connection successful")
                return
            except pymssql.OperationalError as e:
                print(f"OperationalError: {e}")
                if 'Connection reset by peer' in str(e):
                    attempt += 1
                    print(f"Retrying connection... (Attempt {attempt}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                else:
                    break
            except Exception as e:
                print(f"Error: {e}")
                break
        print("Failed to connect to the database after multiple attempts.")
        self.conn = None

    def execute_query(self, query):
        if self.conn is None:
            print("Connection is not established.")
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return rows
        except pymssql.OperationalError as e:
            print(f"OperationalError executing query: {e}")
        except Exception as e:
            print(f"Error executing query: {e}")
        return None

    def close(self):
        if self.conn:
            self.conn.close()
            print("Connection closed")


    def get_credentials(self, username):
        if self.conn is None:
            print("Connection is not established.")
            return None
        
        try:
            cursor = self.conn.cursor()
            query = "SELECT username, password FROM credentials WHERE username = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            if result:
                return {'username': result[0], 'password': result[1]}
            else:
                return None
        except pymssql.OperationalError as e:
            print(f"OperationalError executing query: {e}")
        except Exception as e:
            print(f"Error executing query: {e}")
        return None

