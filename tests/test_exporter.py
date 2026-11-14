import csv
import tempfile
import unittest
from pathlib import Path

from release_service.exporter import export_csv


class ExportCsvTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.artifacts = self.root / "artifacts"
        self.source.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def write_orders(self):
        path = self.source / "pedidos.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["pedido_id", "data_pedido", "cliente_id", "quantidade_pedida"])
            writer.writeheader()
            writer.writerows([
                {"pedido_id": "P-1", "data_pedido": "2026-05-01", "cliente_id": "C-1", "quantidade_pedida": "10"},
                {"pedido_id": "P-2", "data_pedido": "2026-05-02", "cliente_id": "C-2", "quantidade_pedida": "20"},
                {"pedido_id": "P-3", "data_pedido": "2026-05-03", "cliente_id": "C-3", "quantidade_pedida": "30"},
            ])
        return path

    def test_exports_only_selected_columns_and_inclusive_date_range(self):
        self.write_orders()

        path, digest, row_count = export_csv(
            self.source,
            self.artifacts,
            {"file": "pedidos.csv", "columns": ["pedido_id", "quantidade_pedida"], "date_from": "2026-05-02", "date_to": "2026-05-03"},
        )

        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(list(rows[0]), ["pedido_id", "quantidade_pedida"])
        self.assertEqual([row["pedido_id"] for row in rows], ["P-2", "P-3"])
        self.assertEqual(row_count, 2)
        self.assertEqual(len(digest), 64)

    def test_exports_header_when_date_range_has_no_matches(self):
        self.write_orders()

        path, _, row_count = export_csv(
            self.source,
            self.artifacts,
            {"file": "pedidos.csv", "columns": ["pedido_id"], "date_from": "2027-01-01", "date_to": "2027-01-31"},
        )

        with path.open(encoding="utf-8-sig", newline="") as handle:
            self.assertEqual(list(csv.DictReader(handle)), [])
        self.assertEqual(row_count, 0)

    def test_rejects_unknown_file_and_path_traversal(self):
        self.write_orders()
        for filename in ("missing.csv", "../pedidos.csv", "pedidos.csv/../../secret.csv"):
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                export_csv(self.source, self.artifacts, {"file": filename, "columns": ["pedido_id"]})

    def test_rejects_unknown_columns(self):
        self.write_orders()
        with self.assertRaises(ValueError):
            export_csv(self.source, self.artifacts, {"file": "pedidos.csv", "columns": ["senha"]})

    def test_rejects_invalid_date_bounds(self):
        self.write_orders()
        for scope in (
            {"file": "pedidos.csv", "columns": ["pedido_id"], "date_from": "02/05/2026"},
            {"file": "pedidos.csv", "columns": ["pedido_id"], "date_from": "2026-06-01", "date_to": "2026-05-01"},
        ):
            with self.subTest(scope=scope), self.assertRaises(ValueError):
                export_csv(self.source, self.artifacts, scope)


if __name__ == "__main__":
    unittest.main()
