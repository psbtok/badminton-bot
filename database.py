import sqlite3
import os

class Database:
    _instance = None

    def __new__(cls, db_path=None):
        # If instance exists but connection is closed, re-initialize
        if cls._instance and cls._instance.conn is None:
            cls._instance.conn = sqlite3.connect(cls._instance.db_path, check_same_thread=False)
            cls._instance.conn.row_factory = sqlite3.Row
            return cls._instance

        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            
            if db_path is None:
                # Default to data/events.db and respect environment variable
                db_path = os.environ.get('DB_PATH', 'data/events.db')
            
            # Ensure the directory for the database exists
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)

            cls._instance.db_path = db_path
            cls._instance.conn = sqlite3.connect(cls._instance.db_path, check_same_thread=False)
            cls._instance.conn.row_factory = sqlite3.Row
        return cls._instance

    def get_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def execute_query(self, query, params=()):
        cursor = self.get_connection().cursor()
        cursor.execute(query, params)
        return cursor

    def fetch_all(self, query, params=()):
        cursor = self.execute_query(query, params)
        return cursor.fetchall()

    def fetch_one(self, query, params=()):
        cursor = self.execute_query(query, params)
        return cursor.fetchone()

    def execute_script(self, query, params=()):
        cursor = self.get_connection().cursor()
        cursor.execute(query, params)
        self.get_connection().commit()
        return cursor.lastrowid

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.__class__._instance = None

    def delete_db(self):
        self.close()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass
