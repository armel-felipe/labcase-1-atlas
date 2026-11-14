"""Small HTTP boundary for the private Case Atlas release service."""

import hmac
import json
import os
import re
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

MAX_BODY_BYTES = 1_048_576
def create_server(host: str, port: int, service, api_token: str, download_token: str) -> ThreadingHTTPServer:
    if not isinstance(api_token, str) or len(api_token) < 32:
        raise ValueError("CASE_RELEASE_API_TOKEN must contain at least 32 characters")
    if not isinstance(download_token, str) or len(download_token) < 32:
        raise ValueError("CASE_RELEASE_DOWNLOAD_TOKEN must contain at least 32 characters")

    class Handler(BaseHTTPRequestHandler):
        server_version = "CaseAtlasRelease/1.0"

        def log_message(self, format, *args):
            return

        def _json(self, status: int, value: dict):
            body = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _api_authorized(self) -> bool:
            actual = self.headers.get("Authorization", "")
            expected = f"Bearer {api_token}"
            if not hmac.compare_digest(actual, expected):
                self._json(401, {"error": "unauthorized"})
                return False
            return True

        def _download_authorized(self) -> bool:
            actual = self.headers.get("X-Case-Atlas-Gateway-Token", "")
            if not hmac.compare_digest(actual, download_token):
                self._json(401, {"error": "team authentication required"})
                return False
            return True

        def _body(self) -> dict:
            raw_length = self.headers.get("Content-Length")
            try:
                length = int(raw_length or "")
            except ValueError as exc:
                raise ValueError("Content-Length is required") from exc
            if length < 0 or length > MAX_BODY_BYTES:
                raise ValueError("request body is too large")
            if self.headers.get_content_type() != "application/json":
                raise ValueError("Content-Type must be application/json")
            try:
                value = json.loads(self.rfile.read(length))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("request body must be valid JSON") from exc
            if not isinstance(value, dict):
                raise ValueError("request body must be a JSON object")
            return value

        def _error(self, error: Exception):
            if isinstance(error, PermissionError):
                self._json(410, {"error": "release is revoked"})
            elif isinstance(error, FileNotFoundError):
                self._json(404, {"error": "not found"})
            elif isinstance(error, (ValueError, TypeError)):
                self._json(400, {"error": str(error)[:300]})
            else:
                self._json(500, {"error": "internal service error"})

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == "/health":
                self._json(200, {"status": "ok"})
                return
            match = re.fullmatch(r"/v1/requests/([a-f0-9]{32})", path)
            if match:
                if not self._api_authorized():
                    return
                request = service.get_request(match.group(1))
                if request is None:
                    self._json(404, {"error": "not found"})
                else:
                    self._json(200, request)
                return
            match = re.fullmatch(r"/v1/releases/([a-f0-9]{32})", path)
            if match:
                if not self._api_authorized():
                    return
                release = service.get_release(match.group(1))
                if release is None:
                    self._json(404, {"error": "not found"})
                else:
                    self._json(200, release)
                return
            match = re.fullmatch(r"/v1/releases/([a-f0-9]{32})/download", path)
            if match:
                if not self._download_authorized():
                    return
                try:
                    artifact = service.download_path(match.group(1))
                    size = artifact.stat().st_size
                    self.send_response(200)
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Content-Length", str(size))
                    self.send_header("Content-Disposition", f'attachment; filename="case-atlas-{match.group(1)}.csv"')
                    self.send_header("Cache-Control", "private, no-store")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    with artifact.open("rb") as handle:
                        shutil.copyfileobj(handle, self.wfile)
                except (ValueError, PermissionError, FileNotFoundError, OSError) as error:
                    self._error(error)
                return
            self._json(404, {"error": "not found"})

        def do_POST(self):
            if not self._api_authorized():
                return
            path = urlsplit(self.path).path
            try:
                if path == "/v1/requests":
                    result = service.submit_request(self._body())
                    self._json(201, result)
                    return
                if path == "/v1/decision-context":
                    body = self._body()
                    context = service.decision_context(body.get("stakeholder_id"))
                    self._json(200, context)
                    return
                match = re.fullmatch(r"/v1/requests/([a-f0-9]{32})/decision", path)
                if match:
                    body = self._body()
                    result = service.record_decision(match.group(1), body.get("facilitator"), body.get("stakeholder"))
                    self._json(200, result)
                    return
                match = re.fullmatch(r"/v1/releases/([a-f0-9]{32})/revoke", path)
                if match:
                    self._body()
                    if not service.revoke_release(match.group(1)):
                        self._json(404, {"error": "active release not found"})
                    else:
                        self._json(200, {"release_id": match.group(1), "revoked": True})
                    return
                self._json(404, {"error": "not found"})
            except Exception as error:
                self._error(error)

    return ThreadingHTTPServer((host, port), Handler)


def serve_from_environment() -> None:
    source_dir = Path(os.environ["CASE_RELEASE_SOURCE_DIR"])
    storage_dir = Path(os.environ["CASE_RELEASE_STORAGE_DIR"])
    api_token = os.environ["CASE_RELEASE_API_TOKEN"]
    download_token = os.environ["CASE_RELEASE_DOWNLOAD_TOKEN"]
    host = os.environ.get("CASE_RELEASE_HOST", "127.0.0.1")
    port = int(os.environ.get("CASE_RELEASE_PORT", "8091"))
    from .service import ReleaseService

    facilitator_dir = Path(os.environ.get("CASE_RELEASE_FACILITATOR_DIR", source_dir.parent))
    server = create_server(host, port, ReleaseService(source_dir, storage_dir, facilitator_dir=facilitator_dir), api_token, download_token)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
