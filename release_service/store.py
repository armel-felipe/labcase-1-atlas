"""SQLite persistence for requests and published releases."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ReleaseStore:
    def __init__(self, database_path: Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS requests (
                    request_id TEXT PRIMARY KEY,
                    origin_thread_id TEXT NOT NULL,
                    requester_id TEXT NOT NULL,
                    workspace TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    purpose_key TEXT NOT NULL,
                    safeguards TEXT NOT NULL,
                    requested_scope TEXT NOT NULL,
                    status TEXT NOT NULL,
                    decisions TEXT,
                    release_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS releases (
                    release_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL REFERENCES requests(request_id),
                    source_file TEXT NOT NULL,
                    purpose_key TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    artifact_name TEXT NOT NULL,
                    artifact_sha256 TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    row_count INTEGER NOT NULL,
                    parent_release_id TEXT,
                    created_at TEXT NOT NULL,
                    revoked_at TEXT
                );
                CREATE INDEX IF NOT EXISTS releases_reuse_idx
                    ON releases(purpose_key, source_file, created_at);
                """
            )
            request_columns = {row[1] for row in connection.execute("PRAGMA table_info(requests)")}
            if "requester_id" not in request_columns:
                connection.execute("ALTER TABLE requests ADD COLUMN requester_id TEXT NOT NULL DEFAULT 'unknown'")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _request_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        result = dict(row)
        result["requested_scope"] = json.loads(result["requested_scope"])
        result["decisions"] = json.loads(result["decisions"]) if result["decisions"] else None
        return result

    @staticmethod
    def _release_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        result = dict(row)
        result["scope"] = json.loads(result["scope"])
        return result

    def create_request(self, request: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO requests
                   (request_id, origin_thread_id, requester_id, workspace, source_file, purpose, purpose_key,
                    safeguards, requested_scope, status, decisions, release_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', NULL, NULL, ?, ?)""",
                (request["request_id"], request["origin_thread_id"], request["requester_id"], request["workspace"], request["file"],
                 request["purpose"], request["purpose_key"], request["safeguards"],
                 json.dumps(request["scope"], sort_keys=True), request["created_at"], request["created_at"]),
            )

    def get_request(self, request_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            return self._request_dict(connection.execute("SELECT * FROM requests WHERE request_id = ?", (request_id,)).fetchone())

    def all_active_releases(self, purpose_key: str, source_file: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT r.*, q.safeguards AS source_safeguards
                   FROM releases r JOIN requests q ON q.request_id = r.request_id
                   WHERE r.purpose_key = ? AND r.source_file = ? AND r.revoked_at IS NULL
                   ORDER BY r.created_at""",
                (purpose_key, source_file),
            ).fetchall()
            return [self._release_dict(row) for row in rows if row]

    def record_terminal_request(self, request_id: str, status: str, decisions: dict[str, Any]) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE requests SET status = ?, decisions = ?, updated_at = ? WHERE request_id = ? AND status = 'pending'",
                (status, json.dumps(decisions, sort_keys=True), utc_now(), request_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("request is missing or no longer pending")

    def record_reuse(self, request_id: str, release_id: str, decisions: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """UPDATE requests SET status = 'released', decisions = ?, release_id = ?, updated_at = ?
                   WHERE request_id = ? AND status = 'pending'
                     AND EXISTS (SELECT 1 FROM releases WHERE release_id = ? AND revoked_at IS NULL)""",
                (json.dumps(decisions, sort_keys=True), release_id, utc_now(), request_id, release_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("request is missing or no longer pending")

    def create_release(self, release: dict[str, Any], decisions: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                "UPDATE requests SET status = 'released', decisions = ?, release_id = ?, updated_at = ? WHERE request_id = ? AND status = 'pending'",
                (json.dumps(decisions, sort_keys=True), release["release_id"], release["created_at"], release["request_id"]),
            )
            if cursor.rowcount != 1:
                raise ValueError("request is missing or no longer pending")
            connection.execute(
                """INSERT INTO releases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)""",
                (release["release_id"], release["request_id"], release["source_file"], release["purpose_key"],
                 json.dumps(release["scope"], sort_keys=True), release["artifact_name"], release["artifact_sha256"],
                 release["source_sha256"], release["row_count"], release["parent_release_id"], release["created_at"]),
            )

    def get_release(self, release_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT r.*, q.origin_thread_id, q.requester_id AS requested_by FROM releases r
                   JOIN requests q ON q.request_id = r.request_id WHERE r.release_id = ?""",
                (release_id,),
            ).fetchone()
            return self._release_dict(row)

    def revoke_release(self, release_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE releases SET revoked_at = ? WHERE release_id = ? AND revoked_at IS NULL",
                (utc_now(), release_id),
            )
            return cursor.rowcount == 1
