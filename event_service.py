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
