"""SQLite helpers for persistent conversations and chat history."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent.parent / "database" / "chat_history.db"


def _connect() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                mode TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                conversation_id INTEGER,
                created_at TEXT NOT NULL
            )
            """
        )
        columns = {row[1] for row in connection.execute("PRAGMA table_info(messages)")}
        if "conversation_id" not in columns:
            connection.execute("ALTER TABLE messages ADD COLUMN conversation_id INTEGER")


def create_conversation(mode: str, title: str = "New conversation") -> int:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        cursor = connection.execute(
            "INSERT INTO conversations (title, mode, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (title, mode, now, now),
        )
        return int(cursor.lastrowid)


def list_conversations(limit: int = 30) -> list[dict[str, str | int]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, title, mode, created_at, updated_at FROM conversations "
            "ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_conversation(conversation_id: int) -> dict[str, str | int] | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, title, mode, created_at, updated_at FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()
    return dict(row) if row else None


def save_message(role: str, content: str, conversation_id: int | None = None) -> None:
    if role not in {"user", "assistant"}:
        raise ValueError("role must be 'user' or 'assistant'.")

    with _connect() as connection:
        connection.execute(
            "INSERT INTO messages (role, content, conversation_id, created_at) VALUES (?, ?, ?, ?)",
            (role, content, conversation_id, datetime.now(timezone.utc).isoformat()),
        )
        if conversation_id is not None:
            connection.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), conversation_id),
            )


def load_messages(conversation_id: int | None = None, limit: int = 100) -> list[dict[str, str]]:
    with _connect() as connection:
        if conversation_id is None:
            query = "SELECT role, content FROM messages WHERE conversation_id IS NULL ORDER BY id DESC LIMIT ?"
            rows = connection.execute(query, (limit,)).fetchall()
        else:
            query = "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT ?"
            rows = connection.execute(query, (conversation_id, limit)).fetchall()
    return [dict(row) for row in reversed(rows)]


def clear_messages(conversation_id: int | None = None) -> None:
    with _connect() as connection:
        if conversation_id is None:
            connection.execute("DELETE FROM messages")
            connection.execute("DELETE FROM conversations")
        else:
            connection.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            connection.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
