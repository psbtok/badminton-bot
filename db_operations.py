import sqlite3
from datetime import datetime

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

    def get_upcoming_events(self, participant_id=None):
        today_start = datetime.now().strftime('%Y-%m-%d 00:00')
        if participant_id:
            query = """
                SELECT e.date, e.time_start, e.time_end, e.id, e.announce_message_id,
                       (SELECT COUNT(id) FROM event_participants WHERE event_id = e.id AND (canceled IS NULL OR canceled = 0)) as participant_count,
                       e.max_participants,
                       ep.name
                FROM events e
                JOIN event_participants ep ON e.id = ep.event_id
                WHERE ep.participant_id = ? AND (ep.canceled IS NULL OR ep.canceled = 0) AND (e.date || ' ' || e.time_start) >= ? AND (e.canceled IS NULL OR e.canceled = 0)
                ORDER BY e.date, e.time_start
            """
            self.cursor.execute(query, (participant_id, today_start))
        else:
            query = """
                SELECT e.date, e.time_start, e.time_end, e.id, e.private_message_id, e.announce_message_id,
                       (SELECT COUNT(id) FROM event_participants WHERE event_id = e.id AND (canceled IS NULL OR canceled = 0)) as participant_count,
                       e.max_participants
                FROM events e
                WHERE (e.date || ' ' || e.time_start) >= ? AND (e.canceled IS NULL OR e.canceled = 0)
                ORDER BY e.date, e.time_start
            """
            self.cursor.execute(query, (today_start,))
        return self.cursor.fetchall()

    def get_future_events(self):
        today_start = datetime.now().strftime('%Y-%m-%d 00:00')
        query = """
            SELECT e.date, e.time_start, e.time_end, e.id, e.private_message_id, e.announce_message_id,
                   (SELECT COUNT(id) FROM event_participants WHERE event_id = e.id AND (canceled IS NULL OR canceled = 0)) as participant_count,
                   e.max_participants
            FROM events e
            WHERE (e.date || ' ' || e.time_start) >= ? AND (e.canceled IS NULL OR e.canceled = 0)
            ORDER BY e.date, e.time_start
        """
        self.cursor.execute(query, (today_start,))
        return self.cursor.fetchall()

    def create_tables_if_not_exist(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time_start TEXT NOT NULL,
                time_end TEXT NOT NULL,
                creator INTEGER NOT NULL,
                max_participants INTEGER
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                participant_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY(event_id) REFERENCES events(id)
            )
        ''')
        self.conn.commit()

    def cancel_event(self, event_id):
        self.cursor.execute("UPDATE events SET canceled = 1 WHERE id = ?", (event_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()
