import os
import sqlite3
from datetime import datetime, timezone
from services.event_service import EventService

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), 'migrations')

def ensure_migrations_table(conn: sqlite3.Connection):
    conn.execute(
        'CREATE TABLE IF NOT EXISTS _migrations (id TEXT PRIMARY KEY, applied_at TEXT)'
    )
    conn.commit()

def get_applied(conn: sqlite3.Connection):
    cur = conn.execute('SELECT id FROM _migrations')
    return {row[0] for row in cur.fetchall()}

def mark_applied(conn: sqlite3.Connection, migration_id: str):
    conn.execute('INSERT OR REPLACE INTO _migrations (id, applied_at) VALUES (?, ?)', (migration_id, datetime.now(timezone.utc).isoformat()))
    conn.commit()

def run_migrations(migrations_dir: str = MIGRATIONS_DIR):
    if not os.path.isdir(migrations_dir):
        return
    db = EventService()
    conn = db.db.conn
    try:
        ensure_migrations_table(conn)
        applied = get_applied(conn)
        files = sorted(f for f in os.listdir(migrations_dir) if f.endswith('.sql'))
        for fname in files:
            if fname in applied:
                continue
            path = os.path.join(migrations_dir, fname)
            with open(path, 'r', encoding='utf-8') as fh:
                sql = fh.read()
            try:
                # Use executescript to allow multiple statements
                conn.executescript(sql)
                mark_applied(conn, fname)
                print(f"Applied migration: {fname}")
            except sqlite3.OperationalError as e:
                msg = str(e).lower()
                # If error is about duplicate column or already exists, we treat as applied
                if 'duplicate column name' in msg or 'already exists' in msg or 'duplicate' in msg:
                    mark_applied(conn, fname)
                    print(f"Migration {fname} skipped (already applied).")
                else:
                    print(f"Failed to apply migration {fname}: {e}")
                    raise
    finally:
        try:
            db.close()
        except Exception:
            pass

if __name__ == '__main__':
    run_migrations()
