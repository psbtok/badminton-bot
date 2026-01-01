from db_operations import DBOperations

class EventService:
    def __init__(self):
        self.db = DBOperations()

    def create_tables_if_not_exist(self):
        self.db.create_tables_if_not_exist()

    def close(self):
        self.db.close()

    def create_event(self, date, time_start, time_end, creator_id):
        self.db.cursor.execute(
            "INSERT INTO events (date, time_start, time_end, creator) VALUES (?, ?, ?, ?)",
            (date, time_start, time_end, creator_id)
        )
        self.db.conn.commit()
