-- Add joined_at column to event_participants (ISO timestamp text)
ALTER TABLE event_participants ADD COLUMN joined_at TEXT;
