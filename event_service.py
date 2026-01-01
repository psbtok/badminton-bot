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

    def set_event_announcement(self, event_id, chat_id, message_id, thread_id=None):
        cur = self.db.cursor
        cur.execute(
            "UPDATE events SET announce_chat = ?, announce_message_id = ?, announce_thread_id = ? WHERE id = ?",
            (str(chat_id), int(message_id) if message_id is not None else None, int(thread_id) if thread_id is not None else None, int(event_id))
        )
        self.db.conn.commit()

    def get_event_announcement(self, event_id):
        cur = self.db.cursor
        cur.execute("SELECT announce_chat, announce_message_id, announce_thread_id FROM events WHERE id = ?", (event_id,))
        row = cur.fetchone()
        if not row:
            return None, None, None
        return row[0], row[1], row[2]
