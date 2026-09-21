"""Authentication helpers for the Streamlit application."""

from __future__ import annotations

import re
import sqlite3

from utils.database import authenticate_user, create_user

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def register(name: str, email: str, password: str, confirmation: str) -> tuple[bool, str]:
    """Validate and create an account without exposing password details."""
    clean_name = " ".join(name.split()).strip()
    clean_email = email.strip().lower()
    if not clean_name:
        return False, "Enter your name."
    if not EMAIL_PATTERN.match(clean_email):
        return False, "Enter a valid email address."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if password != confirmation:
        return False, "Passwords do not match."
    try:
        create_user(clean_name, clean_email, password)
    except sqlite3.IntegrityError:
        return False, "An account with that email already exists."
    return True, "Account created. You can now log in."


def login(email: str, password: str) -> dict[str, str | int] | None:
    """Return the public user record when the credentials are valid."""
    if not email.strip() or not password:
        return None
    return authenticate_user(email, password)
