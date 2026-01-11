-- Add canceled (0/1) and canceled_at columns to event_participants
-- SQLite does not have a native BOOLEAN type; use INTEGER 0/1 for boolean semantics
ALTER TABLE event_participants ADD COLUMN canceled INTEGER NOT NULL DEFAULT 0;
ALTER TABLE event_participants ADD COLUMN canceled_at TEXT;
