-- Add a column to store the private chat message id for announcements
ALTER TABLE events ADD COLUMN private_message_id INTEGER;
