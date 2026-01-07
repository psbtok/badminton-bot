import datetime as _dt
from datetime import timezone
from database import Database

class EventService:
    def __init__(self):
        self.db = Database()

    def create_tables_if_not_exist(self):
        self.db.execute_script('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time_start TEXT NOT NULL,
                time_end TEXT NOT NULL,
                creator INTEGER NOT NULL,
                max_participants INTEGER
            )
        ''')
        self.db.execute_script('''
            CREATE TABLE IF NOT EXISTS event_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                participant_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY(event_id) REFERENCES events(id)
            )
        ''')

    def close(self):
        self.db.close()

    def create_event(self, date, time_start, time_end, creator_id, max_participants=None):
        return self.db.execute_script(
            "INSERT INTO events (date, time_start, time_end, creator, max_participants) VALUES (?, ?, ?, ?, ?)",
            (date, time_start, time_end, creator_id, max_participants)
        )

    def set_event_announcement(self, event_id, announce_message_id=None, private_message_id=None):
        self.db.execute_script(
            "UPDATE events SET announce_message_id = ?, private_message_id = ? WHERE id = ?",
            (
                int(announce_message_id) if announce_message_id is not None else None,
                int(private_message_id) if private_message_id is not None else None,
                int(event_id),
            ),
        )

    def get_event_announcement(self, event_id):
        row = self.db.fetch_one(
            "SELECT announce_message_id, private_message_id FROM events WHERE id = ?",
            (event_id,)
        )
        if not row:
            return None, None
        return row['announce_message_id'], row['private_message_id']

    def get_user_registrations(self, user_id):
        now = _dt.datetime.now()
        today_str = now.strftime('%Y-%m-%d')
        now_time_str = now.strftime('%H:%M')
        return self.db.fetch_all(
            """
            SELECT p.id, e.id, e.date, e.time_start, e.time_end, p.name
            FROM event_participants p
            JOIN events e ON p.event_id = e.id
            WHERE p.participant_id = ? AND (p.canceled IS NULL OR p.canceled = 0)
            AND (e.date > ? OR (e.date = ? AND e.time_start > ?))
            AND (e.canceled IS NULL OR e.canceled = 0)
            """,
            (user_id, today_str, today_str, now_time_str)
        )

    def get_participant(self, participant_id):
        return self.db.fetch_one(
            "SELECT id, event_id, name FROM event_participants WHERE id = ?",
            (participant_id,)
        )

    def get_event(self, event_id):
        return self.db.fetch_one("SELECT date, time_start, time_end, max_participants FROM events WHERE id = ?", (event_id,))

    def cancel_registration(self, participant_id, canceled_at):
        event_info = self.db.fetch_one("""
            SELECT e.date, e.time_start
            FROM events e
            JOIN event_participants p ON e.id = p.event_id
            WHERE p.id = ?
        """, (participant_id,))

        if event_info:
            event_date_str, event_time_str = event_info['date'], event_info['time_start']
            event_datetime = _dt.datetime.strptime(f"{event_date_str} {event_time_str}", "%Y-%m-%d %H:%M")
            
            if _dt.datetime.now() > event_datetime:
                return False

        self.db.execute_script(
            "UPDATE event_participants SET canceled = 1, canceled_at = ? WHERE id = ?",
            (canceled_at, participant_id)
        )
        return True

    def get_event_participants(self, event_id):
        return self.db.fetch_all("SELECT name, username, joined_at FROM event_participants WHERE event_id = ? AND (canceled IS NULL OR canceled = 0)", (event_id,))

    def get_canceled_participants(self, event_id):
        return self.db.fetch_all(
            "SELECT name, username, canceled_at FROM event_participants WHERE event_id = ? AND canceled = 1 ORDER BY canceled_at",
            (event_id,)
        )

    def get_all_events(self, include_past=False):
        if include_past:
            return self.db.fetch_all("SELECT id, date, time_start, time_end, max_participants, (SELECT COUNT(*) FROM event_participants WHERE event_id = events.id AND (canceled IS NULL OR canceled = 0)) as current_participants FROM events ORDER BY date, time_start")
        else:
            now = _dt.datetime.now()
            today_str = now.strftime('%Y-%m-%d')
            now_time_str = now.strftime('%H:%M')
            
            return self.db.fetch_all("""
                SELECT id, date, time_start, time_end, max_participants, (SELECT COUNT(*) FROM event_participants WHERE event_id = events.id AND (canceled IS NULL OR canceled = 0)) as current_participants
                FROM events 
                WHERE (date > ? OR (date = ? AND time_start > ?)) AND (canceled IS NULL OR canceled = 0)
                ORDER BY date, time_start
            """, (today_str, today_str, now_time_str))

    def add_participant(self, event_id, user_id, name, username, joined_at):
        self.db.execute_script(
            "INSERT INTO event_participants (event_id, participant_id, name, username, joined_at) VALUES (?, ?, ?, ?, ?)",
            (event_id, user_id, name, username, joined_at)
        )

    def get_event_by_id(self, event_id):
        row = self.db.fetch_one("SELECT id, date, time_start, time_end, creator, max_participants, announce_message_id, private_message_id, canceled FROM events WHERE id = ?", (event_id,))
        if not row:
            return None
        
        from models import Event
        return Event(
            id=row['id'],
            date=row['date'],
            time_start=row['time_start'],
            time_end=row['time_end'],
            creator=row['creator'],
            max_participants=row['max_participants'],
            announce_message_id=row['announce_message_id'],
            private_message_id=row['private_message_id'],
            canceled=row['canceled']
        )

    def get_upcoming_events(self, participant_id=None):
        today_start = _dt.datetime.now().strftime('%Y-%m-%d 00:00')
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
            return self.db.fetch_all(query, (participant_id, today_start))
        else:
            query = """
                SELECT e.date, e.time_start, e.time_end, e.id, e.private_message_id, e.announce_message_id,
                       (SELECT COUNT(id) FROM event_participants WHERE event_id = e.id AND (canceled IS NULL OR canceled = 0)) as participant_count,
                       e.max_participants
                FROM events e
                WHERE (e.date || ' ' || e.time_start) >= ? AND (e.canceled IS NULL OR e.canceled = 0)
                ORDER BY e.date, e.time_start
            """
            return self.db.fetch_all(query, (today_start,))

    def get_future_events(self):
        today_start = _dt.datetime.now().strftime('%Y-%m-%d 00:00')
        query = """
            SELECT e.date, e.time_start, e.time_end, e.id, e.private_message_id, e.announce_message_id,
                   (SELECT COUNT(id) FROM event_participants WHERE event_id = e.id AND (canceled IS NULL OR canceled = 0)) as participant_count,
                   e.max_participants
            FROM events e
            WHERE (e.date || ' ' || e.time_start) >= ? AND (e.canceled IS NULL OR e.canceled = 0)
            ORDER BY e.date, e.time_start
        """
        return self.db.fetch_all(query, (today_start,))

    def cancel_event(self, event_id):
        self.db.execute_script("UPDATE events SET canceled = 1 WHERE id = ?", (event_id,))
