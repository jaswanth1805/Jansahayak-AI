"""Persistent capability registry for uploaded documents.

The application has no account system, so each upload receives an unguessable
capability token. Only its hash is stored; possession of the token authorizes
queries and deletion for that one document.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Optional

from app.config import get_settings

DOCUMENT_ID_PATTERN = re.compile(r"^doc_[0-9a-f]{32}$")


def _database_path() -> Path:
    upload_dir = Path(get_settings().UPLOAD_DIR).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir / ".document_registry.sqlite3"


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(_database_path(), timeout=10)
    connection.execute(
        """CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY,
            token_hash TEXT NOT NULL,
            created_at REAL NOT NULL,
            original_filename TEXT NOT NULL,
            revoked INTEGER NOT NULL DEFAULT 0
        )"""
    )
    columns = {row[1] for row in connection.execute("PRAGMA table_info(documents)")}
    if "revoked" not in columns:
        connection.execute("ALTER TABLE documents ADD COLUMN revoked INTEGER NOT NULL DEFAULT 0")
    return connection


def document_file_path(document_id: str) -> Path:
    if not DOCUMENT_ID_PATTERN.fullmatch(document_id):
        raise ValueError("Invalid document identifier")
    return Path(get_settings().UPLOAD_DIR).resolve() / f"{document_id}.pdf"


def register_document(document_id: str, token: str, original_filename: str) -> None:
    if not DOCUMENT_ID_PATTERN.fullmatch(document_id):
        raise ValueError("Invalid document identifier")
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with _connect() as connection:
        connection.execute(
            "INSERT INTO documents(document_id, token_hash, created_at, original_filename) VALUES (?, ?, ?, ?)",
            (document_id, token_hash, time.time(), original_filename[:255]),
        )


def authorize_document(document_id: str, token: Optional[str]) -> bool:
    if not token or not DOCUMENT_ID_PATTERN.fullmatch(document_id):
        return False
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with _connect() as connection:
        row = connection.execute(
            "SELECT token_hash, revoked FROM documents WHERE document_id = ?", (document_id,)
        ).fetchone()
    return bool(row and not row[1] and hmac.compare_digest(row[0], token_hash))


def revoke_document_record(document_id: str) -> None:
    """Revoke a capability immediately while retaining cleanup retry metadata."""
    with _connect() as connection:
        connection.execute("UPDATE documents SET revoked = 1 WHERE document_id = ?", (document_id,))


def registered_document_ids() -> set[str]:
    with _connect() as connection:
        rows = connection.execute("SELECT document_id FROM documents").fetchall()
    return {row[0] for row in rows}


def remove_document_record(document_id: str) -> None:
    with _connect() as connection:
        connection.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))


def expired_document_ids(max_age_hours: int) -> list[str]:
    cutoff = time.time() - max_age_hours * 3600
    with _connect() as connection:
        rows = connection.execute(
            "SELECT document_id FROM documents WHERE created_at < ? OR revoked = 1", (cutoff,)
        ).fetchall()
    return [row[0] for row in rows]


def clean_document_file(document_id: str) -> None:
    try:
        document_file_path(document_id).unlink(missing_ok=True)
    except OSError:
        # Keep the registry entry if the file cannot be removed so cleanup can retry.
        raise

