import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True) if Path(path).parent != Path(".") else None
        with self.connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active'
            );
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, role TEXT NOT NULL,
                content TEXT NOT NULL, created_at TEXT NOT NULL, response_time REAL,
                topic TEXT, FOREIGN KEY(conversation_id) REFERENCES conversations(id)
            );
            CREATE TABLE IF NOT EXISTS analytics_events (
                id TEXT PRIMARY KEY, event_type TEXT NOT NULL, conversation_id TEXT,
                created_at TEXT NOT NULL, topic TEXT, response_time REAL, status TEXT,
                metadata TEXT
            );
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY, message_id TEXT NOT NULL, rating INTEGER NOT NULL,
                comment TEXT, created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_events_created ON analytics_events(created_at);
            """)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_conversation(self, title: str = "New health conversation") -> dict:
        item = (str(uuid4()), title[:100], utc_now(), utc_now())
        with self.connect() as conn:
            conn.execute("INSERT INTO conversations(id,title,created_at,updated_at) VALUES(?,?,?,?)", item)
        return {"id": item[0], "title": item[1], "created_at": item[2], "updated_at": item[3], "status": "active"}

    def get_conversation(self, conversation_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()
            if not row:
                return None
            messages = conn.execute("SELECT * FROM messages WHERE conversation_id=? ORDER BY created_at", (conversation_id,)).fetchall()
        return {**dict(row), "messages": [dict(message) for message in messages]}

    def list_conversations(self) -> list[dict]:
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM conversations ORDER BY updated_at DESC")]

    def add_message(self, conversation_id: str, role: str, content: str, response_time: float | None = None, topic: str | None = None) -> str:
        message_id = str(uuid4())
        now = utc_now()
        with self.connect() as conn:
            conn.execute("INSERT INTO messages VALUES(?,?,?,?,?,?,?)", (message_id, conversation_id, role, content, now, response_time, topic))
            conn.execute("UPDATE conversations SET updated_at=? WHERE id=?", (now, conversation_id))
        return message_id

    def event(self, event_type: str, conversation_id: str | None = None, topic: str | None = None, response_time: float | None = None, status: str | None = None, metadata: dict | None = None) -> None:
        with self.connect() as conn:
            conn.execute("INSERT INTO analytics_events VALUES(?,?,?,?,?,?,?,?)", (str(uuid4()), event_type, conversation_id, utc_now(), topic, response_time, status, json.dumps(metadata or {})))

    def add_feedback(self, message_id: str, rating: int, comment: str | None) -> None:
        with self.connect() as conn:
            conn.execute("INSERT INTO feedback VALUES(?,?,?,?,?)", (str(uuid4()), message_id, rating, (comment or "")[:500], utc_now()))

    def metrics(self) -> dict:
        with self.connect() as conn:
            totals = conn.execute("""SELECT
                COUNT(DISTINCT CASE WHEN event_type='conversation_started' THEN conversation_id END) conversations,
                COUNT(CASE WHEN event_type='user_message_sent' THEN 1 END) questions,
                AVG(CASE WHEN event_type='ai_response_generated' THEN response_time END) avg_response,
                SUM(CASE WHEN event_type='ai_response_generated' AND status='success' THEN 1 ELSE 0 END) successful,
                SUM(CASE WHEN event_type='response_error' THEN 1 ELSE 0 END) errors
                FROM analytics_events""").fetchone()
            topics = [dict(row) for row in conn.execute("SELECT topic, COUNT(*) count FROM analytics_events WHERE event_type='user_message_sent' AND topic IS NOT NULL GROUP BY topic ORDER BY count DESC")]
            feedback = conn.execute("SELECT AVG(rating) score, COUNT(*) count FROM feedback").fetchone()
        questions = totals["questions"] or 0
        return {"conversations": totals["conversations"] or 0, "questions": questions, "avg_response": round(totals["avg_response"] or 0, 2), "success_rate": round((totals["successful"] or 0) / max(1, (totals["successful"] or 0) + (totals["errors"] or 0)) * 100, 1), "satisfaction": round(feedback["score"] or 0, 2), "topics": topics}
