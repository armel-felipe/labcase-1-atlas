import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from release_service.service import ReleaseService


class ReleaseServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.source = root / "source"
        self.storage = root / "storage"
        self.source.mkdir()
        self.storage.mkdir()
        with (self.source / "pedidos.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["pedido_id", "data_pedido", "cliente_id", "quantidade_pedida"])
            writer.writeheader()
            writer.writerows([
                {"pedido_id": "P-1", "data_pedido": "2026-05-01", "cliente_id": "C-1", "quantidade_pedida": "10"},
                {"pedido_id": "P-2", "data_pedido": "2026-05-02", "cliente_id": "C-2", "quantidade_pedida": "20"},
                {"pedido_id": "P-3", "data_pedido": "2026-05-03", "cliente_id": "C-3", "quantidade_pedida": "30"},
            ])
        self.service = ReleaseService(self.source, self.storage)

    def tearDown(self):
        self.temp.cleanup()

    def request(self, thread="thread-1", columns=None, date_from=None, date_to=None, purpose="analisar atrasos"):
        return self.service.submit_request({
            "origin_thread_id": thread,
            "requester_id": "consultor-ana",
            "workspace": "Case Atlas",
            "file": "pedidos.csv",
            "purpose": purpose,
            "safeguards": "somente IDs e volume agregado",
            "columns": columns or ["pedido_id", "data_pedido", "quantidade_pedida"],
            "date_from": date_from,
            "date_to": date_to,
        })

    @staticmethod
    def decision(outcome="complete", columns=None, date_from=None, date_to=None, reason="escopo proporcional"):
        return {
            "outcome": outcome,
            "reason": reason,
            "scope": {
                "file": "pedidos.csv",
                "columns": columns or ["pedido_id", "data_pedido", "quantidade_pedida"],
                "date_from": date_from,
                "date_to": date_to,
            },
        }

    def approve(self, request_id, facilitator=None, stakeholder=None):
        return self.service.record_decision(
            request_id,
            facilitator or self.decision(),
            stakeholder or self.decision(),
        )

    def test_requires_origin_thread_reference(self):
        with self.assertRaises(ValueError):
            self.service.submit_request({"file": "pedidos.csv", "purpose": "analisar"})

    def test_either_roleplay_refusal_blocks_artifact(self):
        request = self.request()

        result = self.approve(request["request_id"], facilitator=self.decision("refuse", reason="sem necessidade"))

        self.assertEqual(result["status"], "refused")
        self.assertIsNone(result["release_id"])
        self.assertEqual(list((self.storage / "artifacts").glob("*.csv")), [])

    def test_clarification_does_not_create_artifact(self):
        request = self.request()

        result = self.approve(request["request_id"], stakeholder=self.decision("clarify", reason="qual janela?"))

        self.assertEqual(result["status"], "clarify")
        self.assertIsNone(result["release_id"])
        self.assertEqual(list((self.storage / "artifacts").glob("*.csv")), [])

    def test_partial_scopes_publish_only_intersection(self):
        request = self.request()
        facilitator = self.decision("partial", ["pedido_id", "data_pedido"], "2026-05-02", "2026-05-03")
        stakeholder = self.decision("partial", ["pedido_id", "quantidade_pedida"], "2026-05-03", None)

        result = self.approve(request["request_id"], facilitator, stakeholder)

        self.assertEqual(result["status"], "released")
        self.assertEqual(result["scope"]["columns"], ["pedido_id"])
        self.assertEqual(result["scope"]["date_from"], "2026-05-03")
        self.assertEqual(result["scope"]["date_to"], "2026-05-03")

    def test_exact_request_reuses_release_across_threads(self):
        first = self.request("thread-1")
        release = self.approve(first["request_id"])
        second = self.request("thread-2")

        self.assertEqual(second["status"], "released")
        self.assertEqual(second["release_id"], release["release_id"])
        self.assertTrue(second["reused"])
        self.assertEqual(self.service.get_request(second["request_id"])["status"], "released")
        self.assertEqual(len(list((self.storage / "artifacts").glob("*.csv"))), 1)

    def test_narrower_request_creates_derivative_of_existing_release(self):
        broad = self.request(date_from="2026-05-01", date_to="2026-05-03")
        original = self.approve(broad["request_id"])
        narrow = self.request("thread-2", columns=["pedido_id"], date_from="2026-05-02", date_to="2026-05-03")

        self.assertEqual(narrow["status"], "released")
        self.assertEqual(narrow["parent_release_id"], original["release_id"])
        self.assertEqual(narrow["scope"]["columns"], ["pedido_id"])
        self.assertTrue(narrow["reused"])

    def test_changed_safeguards_require_fresh_negotiation(self):
        first = self.request()
        self.approve(first["request_id"])
        second = self.service.submit_request({
            "origin_thread_id": "thread-2",
            "requester_id": "consultor-ana",
            "workspace": "Case Atlas",
            "file": "pedidos.csv",
            "purpose": "analisar atrasos",
            "safeguards": "agora quero nomes e dados individuais",
            "columns": ["pedido_id", "data_pedido", "quantidade_pedida"],
            "date_from": None,
            "date_to": None,
        })

        self.assertEqual(second["status"], "pending")
        self.assertNotIn("release_id", second)

    def test_changed_source_requires_fresh_negotiation(self):
        first = self.request()
        self.approve(first["request_id"])
        with (self.source / "pedidos.csv").open("a", encoding="utf-8") as handle:
            handle.write("P-4,2026-05-04,C-4,40\n")

        second = self.request("thread-2")

        self.assertEqual(second["status"], "pending")
        self.assertNotIn("release_id", second)

    def test_decision_scope_cannot_silently_drop_unsupported_row_filter(self):
        request = self.request()
        restricted = self.decision()
        restricted["scope"]["filters"] = {"cliente_id": "C-1"}

        with self.assertRaisesRegex(ValueError, "unsupported filters"):
            self.approve(request["request_id"], facilitator=restricted)

        self.assertEqual(self.service.get_request(request["request_id"])["status"], "pending")

    def test_release_persists_origin_and_hash_provenance(self):
        request = self.request("original-thread")

        result = self.approve(request["request_id"])
        release = self.service.get_release(result["release_id"])

        self.assertEqual(release["origin_thread_id"], "original-thread")
        self.assertEqual(release["requested_by"], "consultor-ana")
        self.assertEqual(len(release["artifact_sha256"]), 64)
        self.assertEqual(len(release["source_sha256"]), 64)
        self.assertTrue(release["created_at"])

    def test_revoked_release_cannot_be_downloaded(self):
        request = self.request()
        result = self.approve(request["request_id"])

        self.service.revoke_release(result["release_id"])

        with self.assertRaises(PermissionError):
            self.service.download_path(result["release_id"])

    def test_source_symlink_cannot_escape_configured_data_room(self):
        outside = self.source.parent / "outside.csv"
        outside.write_text("pedido_id,data_pedido,quantidade_pedida\nSECRET,2026-05-01,1\n", encoding="utf-8")
        (self.source / "pedidos.csv").unlink()
        (self.source / "pedidos.csv").symlink_to(outside)
        original_read_bytes = Path.read_bytes
        outside_reads = []

        def observe_reads(path):
            if path.resolve() == outside.resolve():
                outside_reads.append(path)
            return original_read_bytes(path)

        with patch.object(Path, "read_bytes", observe_reads):
            with self.assertRaises(ValueError):
                self.request()

        self.assertEqual(outside_reads, [])
        self.assertEqual(list((self.storage / "artifacts").glob("*.csv")), [])


if __name__ == "__main__":
    unittest.main()
