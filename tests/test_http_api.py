import csv
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from release_service.http_api import create_server
from release_service.service import ReleaseService


class HttpApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        source = root / "source"
        storage = root / "storage"
        source.mkdir()
        (root / "guia_facilitador.md").write_text(
            "## Política de liberação de informação\nPolítica comum.\n\n"
            "### Critérios de concessão\nFinalidade e escopo.\n\n"
            "### Seis perfis e respostas\n|Stakeholder|Tendência|\n|---|---|\n|Comercial Ana Paiva|Agregado.|\n\n"
            "## Entrevistas — segredos de personagem\n- **Ana:** perfil reservado.\n\n"
            "## Eventos inesperados e evolução\nOutro conteúdo.\n",
            encoding="utf-8",
        )
        with (source / "pedidos.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["pedido_id", "data_pedido", "quantidade_pedida"])
            writer.writeheader()
            writer.writerow({"pedido_id": "P-1", "data_pedido": "2026-05-01", "quantidade_pedida": "10"})
        self.service = ReleaseService(source, storage)
        self.api_token = "a" * 48
        self.download_token = "d" * 48
        self.server = create_server("127.0.0.1", 0, self.service, self.api_token, self.download_token)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def call(self, method, path, body=None, headers=None, expect_error=None):
        data = json.dumps(body).encode() if body is not None else None
        request_headers = dict(headers or {})
        if data is not None:
            request_headers.setdefault("Content-Type", "application/json")
        request = Request(self.base + path, data=data, method=method, headers=request_headers)
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, response.headers, response.read()
        except HTTPError as error:
            if expect_error is not None:
                self.assertEqual(error.code, expect_error)
                return error.code, error.headers, error.read()
            raise

    def request_body(self):
        return {
            "origin_thread_id": "thread-1",
            "requester_id": "consultor-ana",
            "workspace": "Case Atlas",
            "file": "pedidos.csv",
            "purpose": "investigar atrasos",
            "columns": ["pedido_id", "data_pedido"],
        }

    def test_mutations_require_api_bearer_token(self):
        self.call("POST", "/v1/requests", self.request_body(), expect_error=401)

        status, _, body = self.call("POST", "/v1/requests", self.request_body(), {"Authorization": f"Bearer {self.api_token}"})

        self.assertEqual(status, 201)
        request_id = json.loads(body)["request_id"]
        self.assertEqual(json.loads(body)["status"], "pending")
        _, _, status_body = self.call("GET", f"/v1/requests/{request_id}", headers={"Authorization": f"Bearer {self.api_token}"})
        self.assertEqual(json.loads(status_body)["origin_thread_id"], "thread-1")
        self.assertEqual(json.loads(status_body)["requester_id"], "consultor-ana")

    def test_decision_and_download_need_distinct_credentials(self):
        _, _, body = self.call("POST", "/v1/requests", self.request_body(), {"Authorization": f"Bearer {self.api_token}"})
        request_id = json.loads(body)["request_id"]
        decision = {"outcome": "complete", "reason": "escopo necessário", "scope": {"file": "pedidos.csv", "columns": ["pedido_id", "data_pedido"]}}
        decision_path = f"/v1/requests/{request_id}/decision"
        _, _, decision_body = self.call(
            "POST", decision_path, {"facilitator": decision, "stakeholder": decision},
            {"Authorization": f"Bearer {self.api_token}"},
        )
        release_id = json.loads(decision_body)["release_id"]

        self.call("GET", f"/v1/releases/{release_id}/download", expect_error=401)
        status, headers, content = self.call("GET", f"/v1/releases/{release_id}/download", headers={"X-Case-Atlas-Gateway-Token": self.download_token})

        self.assertEqual(status, 200)
        self.assertIn("attachment;", headers["Content-Disposition"])
        self.assertEqual(content.decode("utf-8-sig").splitlines()[0], "pedido_id,data_pedido")

    def test_bad_json_and_unknown_routes_return_client_errors(self):
        request = Request(self.base + "/v1/requests", data=b"{bad", method="POST", headers={"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"})
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=3)
        self.assertEqual(caught.exception.code, 400)
        self.call("GET", "/v1/unknown", expect_error=404)

    def test_unknown_request_and_release_ids_return_not_found(self):
        auth = {"Authorization": f"Bearer {self.api_token}"}
        unknown_id = "f" * 32
        self.call("GET", f"/v1/requests/{unknown_id}", headers=auth, expect_error=404)
        self.call("GET", f"/v1/releases/{unknown_id}/download", headers={"X-Case-Atlas-Gateway-Token": self.download_token}, expect_error=404)

    def test_decision_context_requires_api_auth_and_returns_selected_persona_only(self):
        body = {"stakeholder_id": "ana"}
        self.call("POST", "/v1/decision-context", body, expect_error=401)

        status, _, result = self.call("POST", "/v1/decision-context", body, {"Authorization": f"Bearer {self.api_token}"})
        decoded = json.loads(result)
        self.assertEqual(status, 200)
        self.assertIn("Política comum", decoded["policy"])
        self.assertIn("perfil reservado", decoded["stakeholder_profile"])

    def test_revoked_release_returns_gone(self):
        _, _, body = self.call("POST", "/v1/requests", self.request_body(), {"Authorization": f"Bearer {self.api_token}"})
        request_id = json.loads(body)["request_id"]
        decision = {"outcome": "complete", "reason": "escopo necessário", "scope": {"file": "pedidos.csv", "columns": ["pedido_id", "data_pedido"]}}
        _, _, body = self.call("POST", f"/v1/requests/{request_id}/decision", {"facilitator": decision, "stakeholder": decision}, {"Authorization": f"Bearer {self.api_token}"})
        release_id = json.loads(body)["release_id"]
        auth = {"Authorization": f"Bearer {self.api_token}"}
        self.call("POST", f"/v1/releases/{release_id}/revoke", {}, auth)

        self.call("GET", f"/v1/releases/{release_id}/download", headers={"X-Case-Atlas-Gateway-Token": self.download_token}, expect_error=410)


if __name__ == "__main__":
    unittest.main()
