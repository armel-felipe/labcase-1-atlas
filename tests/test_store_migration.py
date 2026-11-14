import sqlite3
import tempfile
import unittest
from pathlib import Path

from release_service.store import ReleaseStore


class StoreMigrationTests(unittest.TestCase):
    def test_existing_request_database_gains_requester_id(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "releases.sqlite3"
            with sqlite3.connect(database) as connection:
                connection.execute(
                    """CREATE TABLE requests (
                        request_id TEXT PRIMARY KEY,
                        origin_thread_id TEXT NOT NULL,
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
                    )"""
                )

            store = ReleaseStore(database)
            store.create_request({
                "request_id": "request-1",
                "origin_thread_id": "thread-1",
                "requester_id": "consultor-ana",
                "workspace": "Case Atlas",
                "file": "pedidos.csv",
                "purpose": "análise",
                "purpose_key": "análise",
                "safeguards": "",
                "scope": {"file": "pedidos.csv", "columns": ["pedido_id"], "date_from": None, "date_to": None},
                "created_at": "2026-11-14T00:00:00+00:00",
            })

            self.assertEqual(store.get_request("request-1")["requester_id"], "consultor-ana")


if __name__ == "__main__":
    unittest.main()
