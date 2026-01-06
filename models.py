class Event:
    def __init__(self, id, date, time_start, time_end, creator, max_participants, announce_message_id, private_message_id, canceled):
        self.id = id
        self.date = date
        self.time_start = time_start
        self.time_end = time_end
        self.creator = creator
        self.max_participants = max_participants
        self.announce_message_id = announce_message_id
        self.private_message_id = private_message_id
        self.canceled = canceled
