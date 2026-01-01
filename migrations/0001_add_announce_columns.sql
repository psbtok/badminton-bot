-- Add announce columns to events table (idempotent via runner)
ALTER TABLE events ADD COLUMN announce_chat TEXT;
ALTER TABLE events ADD COLUMN announce_message_id INTEGER;
ALTER TABLE events ADD COLUMN announce_thread_id INTEGER;
