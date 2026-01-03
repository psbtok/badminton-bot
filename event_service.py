import datetime as _dt
from datetime import timezone
from db_operations import DBOperations

class EventService:
    def __init__(self):
        self.db = DBOperations()

    def create_tables_if_not_exist(self):
        self.db.create_tables_if_not_exist()

    def close(self):
        self.db.close()

    def create_event(self, date, time_start, time_end, creator_id):
        cur = self.db.cursor
        cur.execute(
            "INSERT INTO events (date, time_start, time_end, creator) VALUES (?, ?, ?, ?)",
            (date, time_start, time_end, creator_id)
        )
        self.db.conn.commit()
        return cur.lastrowid

    def set_event_announcement(self, event_id, announce_message_id=None, private_message_id=None):
        cur = self.db.cursor
        cur.execute(
            "UPDATE events SET announce_message_id = ?, private_message_id = ? WHERE id = ?",
            (
                int(announce_message_id) if announce_message_id is not None else None,
                int(private_message_id) if private_message_id is not None else None,
                int(event_id),
            ),
        )
        self.db.conn.commit()

    def get_event_announcement(self, event_id):
        cur = self.db.cursor
        cur.execute(
            "SELECT announce_message_id, private_message_id FROM events WHERE id = ?",
            (event_id,)
        )
        row = cur.fetchone()
        if not row:
            return None, None
        return row[0], row[1]

    def get_user_registrations(self, user_id):
        cur = self.db.cursor
        now_utc = _dt.datetime.now(timezone.utc)
        today_str = now_utc.strftime('%Y-%m-%d')
        now_time_str = now_utc.strftime('%H:%M')
        cur.execute(
            """
            SELECT p.id, e.id, e.date, e.time_start, e.time_end, p.name
            FROM event_participants p
            JOIN events e ON p.event_id = e.id
            WHERE p.participant_id = ? AND (p.canceled IS NULL OR p.canceled = 0)
            AND (e.date > ? OR (e.date = ? AND e.time_start > ?))
            """,
            (user_id, today_str, today_str, now_time_str)
        )
        return cur.fetchall()

    def get_participant(self, participant_id):
        cur = self.db.cursor
        cur.execute(
            "SELECT id, event_id, name FROM event_participants WHERE id = ?",
            (participant_id,)
        )
        return cur.fetchone()

    def get_event(self, event_id):
        cur = self.db.cursor
        cur.execute("SELECT date, time_start, time_end FROM events WHERE id = ?", (event_id,))
        return cur.fetchone()

    def cancel_registration(self, participant_id, canceled_at):
        cur = self.db.cursor
        # Check if the event has already started
        event_info = cur.execute("""
            SELECT e.date, e.time_start
            FROM events e
            JOIN event_participants p ON e.id = p.event_id
            WHERE p.id = ?
        """, (participant_id,)).fetchone()

        if event_info:
            event_date_str, event_time_str = event_info
            event_datetime = _dt.datetime.strptime(f"{event_date_str} {event_time_str}", "%Y-%m-%d %H:%M")
            
            # Make event_datetime timezone-aware (assuming UTC, adjust if different)
            event_datetime = event_datetime.replace(tzinfo=timezone.utc)

            if _dt.datetime.now(timezone.utc) > event_datetime:
                return False  # Event has already started

        cur.execute(
            "UPDATE event_participants SET canceled = 1, canceled_at = ? WHERE id = ?",
            (canceled_at, participant_id)
        )
        self.db.conn.commit()
        return True

    def get_event_participants(self, event_id):
        cur = self.db.cursor
        cur.execute(
            "SELECT name, joined_at FROM event_participants WHERE event_id = ? AND (canceled IS NULL OR canceled = 0) ORDER BY joined_at",
            (event_id,)
        )
        return cur.fetchall()

    def get_all_events(self, include_past=False):
        cur = self.db.cursor
        if include_past:
            cur.execute("SELECT id, date, time_start, time_end FROM events ORDER BY date, time_start")
        else:
            now_utc = _dt.datetime.now(timezone.utc)
            today_str = now_utc.strftime('%Y-%m-%d')
            now_time_str = now_utc.strftime('%H:%M')
            
            cur.execute("""
                SELECT id, date, time_start, time_end 
                FROM events 
                WHERE date > ? OR (date = ? AND time_start > ?)
                ORDER BY date, time_start
            """, (today_str, today_str, now_time_str))
        return cur.fetchall()

    def add_participant(self, event_id, user_id, name, joined_at):
        cur = self.db.cursor
        cur.execute(
            "INSERT INTO event_participants (event_id, participant_id, name, joined_at) VALUES (?, ?, ?, ?)",
            (event_id, user_id, name, joined_at)
        )
        self.db.conn.commit()
