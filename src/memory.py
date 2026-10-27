"""SQLite persistence. Every read/write includes the user boundary."""
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from src.privacy import contains_secret, safe_memory

MEMORY_KEYS = {"workspace_plan", "project_region", "project_name", "response_style", "work_goal"}


def now():
    return datetime.now(timezone.utc).isoformat()


class MemoryStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS sessions (
                    user_id TEXT NOT NULL, session_id TEXT NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, session_id));
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY, user_id TEXT NOT NULL, session_id TEXT NOT NULL,
                    role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id, session_id) REFERENCES sessions(user_id, session_id));
                CREATE TABLE IF NOT EXISTS memories (
                    user_id TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL,
                    provenance TEXT NOT NULL, updated_at TEXT NOT NULL,
                    PRIMARY KEY(user_id, key));
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA secure_delete=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def new_session(self, user_id):
        session_id = str(uuid.uuid4())
        with self.connection() as db:
            db.execute("INSERT INTO sessions VALUES (?,?,?)", (user_id, session_id, now()))
        return session_id

    def sessions(self, user_id):
        with self.connection() as db:
            return [r[0] for r in db.execute(
                "SELECT session_id FROM sessions WHERE user_id=? ORDER BY created_at DESC", (user_id,))]

    def _owned(self, db, user_id, session_id):
        if not db.execute("SELECT 1 FROM sessions WHERE user_id=? AND session_id=?",
                          (user_id, session_id)).fetchone():
            raise ValueError("Session does not belong to the selected user")

    def add_exchange(self, user_id, session_id, question, answer):
        if contains_secret(question) or contains_secret(answer):
            raise ValueError("Credentials cannot be stored in conversation history")
        with self.connection() as db:
            self._owned(db, user_id, session_id)
            db.executemany("INSERT INTO messages(user_id,session_id,role,content,created_at) VALUES (?,?,?,?,?)",
                           [(user_id, session_id, role, content, now()) for role, content in
                            [("user", question), ("assistant", answer)]])

    def history(self, user_id, session_id, limit=12):
        with self.connection() as db:
            self._owned(db, user_id, session_id)
            return [dict(r) for r in reversed(db.execute(
                "SELECT role,content FROM messages WHERE user_id=? AND session_id=? ORDER BY id DESC LIMIT ?",
                (user_id, session_id, limit)).fetchall())]

    def memories(self, user_id):
        with self.connection() as db:
            return [dict(r) for r in db.execute(
                "SELECT key,value,provenance,updated_at FROM memories WHERE user_id=? ORDER BY key", (user_id,))]

    def save(self, user_id, key, value, provenance="user instruction"):
        self.save_many(user_id, {key: value}, provenance)

    def save_many(self, user_id, updates, provenance="user statement"):
        for key, value in updates.items():
            if key not in MEMORY_KEYS or not isinstance(value, str) or not value.strip() or not safe_memory(value):
                raise ValueError("Only non-sensitive workspace context and preferences can be remembered")
            if key == "workspace_plan" and value.strip() not in {"Launch", "Team", "Enterprise"}:
                raise ValueError("Workspace plan must be Launch, Team or Enterprise")
            if key == "project_region" and value.strip() not in {"US", "EU"}:
                raise ValueError("Project region must be US or EU")
        with self.connection() as db:
            old = {r[0]: r[1] for r in db.execute("SELECT key,value FROM memories WHERE user_id=?", (user_id,))}
            # A correction invalidates past context, including in separate sessions.
            if any(k in old and old[k] != v for k, v in updates.items()):
                db.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
            for key, value in updates.items():
                db.execute("INSERT INTO memories VALUES (?,?,?,?,?) ON CONFLICT(user_id,key) DO UPDATE SET "
                           "value=excluded.value,provenance=excluded.provenance,updated_at=excluded.updated_at",
                           (user_id, key, value.strip(), provenance, now()))

    def forget(self, user_id, key=None):
        if key is not None and key not in MEMORY_KEYS:
            raise ValueError("Unknown memory key")
        with self.connection() as db:
            if key is None:
                db.execute("DELETE FROM memories WHERE user_id=?", (user_id,))
            else:
                db.execute("DELETE FROM memories WHERE user_id=? AND key=?", (user_id, key))
            # No historical message can silently reconstruct deleted memory.
            db.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
        # Checkpoint removes deleted WAL pages where SQLite permits it.
        with self.connection() as db:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
