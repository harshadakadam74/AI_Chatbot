"""SQLite helpers for persistent conversations and chat history."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import bcrypt

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
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                mode TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                chat_id INTEGER,
                conversation_id INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
            )
            """
        )
        columns = {row[1] for row in connection.execute("PRAGMA table_info(messages)")}
        if "chat_id" not in columns:
            connection.execute("ALTER TABLE messages ADD COLUMN chat_id INTEGER")
        if "conversation_id" not in columns:
            connection.execute("ALTER TABLE messages ADD COLUMN conversation_id INTEGER")


def create_user(name: str, email: str, password: str) -> int:
    clean_name = " ".join(name.split()).strip()
    clean_email = email.strip().lower()
    if not clean_name or not clean_email or not password:
        raise ValueError("Name, email, and password are required.")
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        cursor = connection.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (clean_name, clean_email, password_hash, now),
        )
        return int(cursor.lastrowid)


def authenticate_user(email: str, password: str) -> dict[str, str | int] | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
    if not row or not bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
        return None
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def create_conversation(user_id: int, mode: str, title: str = "New conversation") -> int:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        cursor = connection.execute(
            "INSERT INTO chats (user_id, title, mode, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, mode, now, now),
        )
        return int(cursor.lastrowid)


def list_conversations(user_id: int, limit: int = 30) -> list[dict[str, str | int]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, title, mode, created_at, updated_at FROM chats "
            "WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def get_conversation(conversation_id: int, user_id: int) -> dict[str, str | int] | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, title, mode, created_at, updated_at FROM chats WHERE id = ? AND user_id = ?",
            (conversation_id, user_id),
        ).fetchone()
    return dict(row) if row else None


def update_conversation_title(conversation_id: int, user_id: int, title: str) -> None:
    """Update a conversation title while keeping it short in the sidebar."""
    clean_title = " ".join(title.split()).strip()[:48]
    if not clean_title:
        return
    with _connect() as connection:
        connection.execute(
            "UPDATE chats SET title = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (clean_title, datetime.now(timezone.utc).isoformat(), conversation_id, user_id),
        )


def save_message(role: str, content: str, chat_id: int, user_id: int) -> None:
    if role not in {"user", "assistant"}:
        raise ValueError("role must be 'user' or 'assistant'.")

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO messages (role, content, chat_id, created_at)
            SELECT ?, ?, id, ? FROM chats WHERE id = ? AND user_id = ?
            """,
            (role, content, datetime.now(timezone.utc).isoformat(), chat_id, user_id),
        )
        if connection.total_changes == 0:
            raise PermissionError("Chat does not belong to the current user.")
        connection.execute(
            "UPDATE chats SET updated_at = ? WHERE id = ? AND user_id = ?",
            (datetime.now(timezone.utc).isoformat(), chat_id, user_id),
        )


def load_messages(chat_id: int, user_id: int, limit: int = 100) -> list[dict[str, str]]:
    with _connect() as connection:
        query = """
            SELECT messages.role, messages.content
            FROM messages
            INNER JOIN chats ON chats.id = messages.chat_id
            WHERE messages.chat_id = ? AND chats.user_id = ?
            ORDER BY messages.id DESC LIMIT ?
        """
        rows = connection.execute(query, (chat_id, user_id, limit)).fetchall()
    return [dict(row) for row in reversed(rows)]


def clear_messages(chat_id: int, user_id: int) -> None:
    with _connect() as connection:
        connection.execute(
            "DELETE FROM messages WHERE chat_id = ? AND chat_id IN (SELECT id FROM chats WHERE user_id = ?)",
            (chat_id, user_id),
        )
        connection.execute("DELETE FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id))
