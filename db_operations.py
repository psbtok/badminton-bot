import sqlite3

class DBOperations:
    def delete_db(self):
        import os
        self.close()
        self.conn = None
        self.cursor = None
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass  # Optionally, log or handle error
    
    def __init__(self, db_path='events.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def create_tables_if_not_exist(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time_start TEXT NOT NULL,
                time_end TEXT NOT NULL,
                creator INTEGER NOT NULL
                , announce_chat TEXT
                , announce_message_id INTEGER
                , announce_thread_id INTEGER
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                participant_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                joined_at TEXT,
                FOREIGN KEY(event_id) REFERENCES events(id)
            )
        ''')
        self.conn.commit()

    def close(self):
        self.conn.close()
