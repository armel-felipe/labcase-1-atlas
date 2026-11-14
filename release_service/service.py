"""Release workflow: consensus, deterministic export, durable provenance."""

import hashlib
import uuid
from datetime import date
from pathlib import Path
from typing import Any

from .catalog import CATALOG
from .decision_context import build_decision_context
from .exporter import export_csv
from .store import ReleaseStore, utc_now

OUTCOMES = {"complete", "partial", "clarify", "refuse"}


def _text(value: Any, name: str, maximum: int, required: bool = True) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be text")
    value = value.strip()
    if (required and not value) or len(value) > maximum:
        raise ValueError(f"{name} is empty or too long")
    return value


def _bound(value: Any, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{name} must use YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must use YYYY-MM-DD") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{name} must use YYYY-MM-DD")
    return value


def _scope(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("scope must be an object")
    unexpected = set(value) - {"file", "columns", "date_from", "date_to"}
    if unexpected:
        raise ValueError("scope contains unsupported filters or fields")
    filename = value.get("file")
    if filename not in CATALOG:
        raise ValueError("file is not in the release catalog")
    columns = value.get("columns")
    if not isinstance(columns, list) or not columns or any(not isinstance(col, str) for col in columns):
        raise ValueError("columns must be a non-empty list")
    source = CATALOG[filename]
    if len(columns) != len(set(columns)) or any(column not in source.columns for column in columns):
        raise ValueError("scope contains duplicate or unapproved columns")
    lower, upper = _bound(value.get("date_from"), "date_from"), _bound(value.get("date_to"), "date_to")
    if (lower or upper) and not source.date_column:
        raise ValueError("date filtering is not supported for this source")
    if lower and upper and lower > upper:
        raise ValueError("date_from must be on or before date_to")
    return {"file": filename, "columns": [c for c in source.columns if c in columns], "date_from": lower, "date_to": upper}


def _purpose_key(purpose: str) -> str:
    return " ".join(purpose.casefold().split())


def _normalize_decision(value: Any, role: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{role} decision must be an object")
    outcome = value.get("outcome")
    if outcome not in OUTCOMES:
        raise ValueError(f"{role} outcome is invalid")
    result = {"outcome": outcome, "reason": _text(value.get("reason"), f"{role}.reason", 2000)}
    if outcome in {"complete", "partial"}:
        result["scope"] = _scope(value.get("scope"))
    elif value.get("scope") is not None:
        result["scope"] = _scope(value["scope"])
    return result


def _intersection(requested: dict[str, Any], facilitator: dict[str, Any], stakeholder: dict[str, Any]) -> dict[str, Any] | None:
    scopes = [facilitator.get("scope"), stakeholder.get("scope")]
    if any(scope is None or scope["file"] != requested["file"] for scope in scopes):
        return None
    columns = set(requested["columns"])
    for scope in scopes:
        columns.intersection_update(scope["columns"])
    if not columns:
        return None
    lower_values = [scope["date_from"] for scope in [requested, *scopes] if scope["date_from"]]
    upper_values = [scope["date_to"] for scope in [requested, *scopes] if scope["date_to"]]
    lower = max(lower_values) if lower_values else None
    upper = min(upper_values) if upper_values else None
    if lower and upper and lower > upper:
        return None
    return {"file": requested["file"], "columns": [c for c in CATALOG[requested["file"]].columns if c in columns], "date_from": lower, "date_to": upper}


def _scope_covers(parent: dict[str, Any], child: dict[str, Any]) -> bool:
    if parent["file"] != child["file"] or not set(child["columns"]).issubset(parent["columns"]):
        return False
    if parent["date_from"] and (not child["date_from"] or child["date_from"] < parent["date_from"]):
        return False
    if parent["date_to"] and (not child["date_to"] or child["date_to"] > parent["date_to"]):
        return False
    return True


class ReleaseService:
    def __init__(self, source_dir: Path, storage_dir: Path, database_path: Path | None = None, facilitator_dir: Path | None = None):
        self.source_dir = Path(source_dir).resolve()
        self.storage_dir = Path(storage_dir).resolve()
        self.facilitator_dir = Path(facilitator_dir or self.source_dir.parent).resolve()
        self.artifact_dir = self.storage_dir / "artifacts"
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.store = ReleaseStore(database_path or self.storage_dir / "releases.sqlite3")

    def decision_context(self, stakeholder_id: str) -> dict[str, str]:
        guide_path = (self.facilitator_dir / "guia_facilitador.md").resolve()
        try:
            guide_path.relative_to(self.facilitator_dir)
        except ValueError as exc:
            raise ValueError("facilitator guide escapes configured directory") from exc
        if not guide_path.is_file():
            raise FileNotFoundError("facilitator guide is unavailable")
        guide_text = guide_path.read_text(encoding="utf-8")
        return build_decision_context(guide_text, stakeholder_id)

    def submit_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("request body must be an object")
        origin = _text(payload.get("origin_thread_id"), "origin_thread_id", 300)
        requester = _text(payload.get("requester_id"), "requester_id", 200)
        workspace = _text(payload.get("workspace", "Case Atlas"), "workspace", 100)
        if workspace != "Case Atlas":
            raise ValueError("workspace must be Case Atlas")
        purpose = _text(payload.get("purpose"), "purpose", 2000)
        safeguards = _text(payload.get("safeguards", ""), "safeguards", 2000, required=False)
        scope = _scope({key: payload.get(key) for key in ("file", "columns", "date_from", "date_to")})
        now = utc_now()
        request = {
            "request_id": uuid.uuid4().hex,
            "origin_thread_id": origin,
            "requester_id": requester,
            "workspace": workspace,
            "file": scope["file"],
            "purpose": purpose,
            "purpose_key": _purpose_key(purpose),
            "safeguards": safeguards,
            "scope": scope,
            "created_at": now,
        }
        self.store.create_request(request)
        result = {"request_id": request["request_id"], "status": "pending", "origin_thread_id": origin}
        reuse = self._reuse_existing(request)
        if reuse:
            reuse.update({"request_id": request["request_id"], "status": "released", "reused": True})
            return reuse
        return result

    def _reuse_existing(self, request: dict[str, Any]) -> dict[str, Any] | None:
        scope = request["scope"]
        source_path = (self.source_dir / scope["file"]).resolve()
        try:
            source_path.relative_to(self.source_dir)
        except ValueError as exc:
            raise ValueError("source file escapes configured directory") from exc
        if not source_path.is_file():
            return None
        source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        candidates = self.store.all_active_releases(request["purpose_key"], scope["file"])
        for release in candidates:
            if (
                release["scope"] == scope
                and _purpose_key(release["source_safeguards"]) == _purpose_key(request["safeguards"])
                and release["source_sha256"] == source_hash
            ):
                self.store.record_reuse(request["request_id"], release["release_id"], {
                    "reuse": "same-purpose-and-scope",
                    "source_release_id": release["release_id"],
                })
                return self._public_release(release)
        parents = [
            release for release in candidates
            if release["source_sha256"] == source_hash
            and _purpose_key(release["source_safeguards"]) == _purpose_key(request["safeguards"])
            and _scope_covers(release["scope"], scope)
        ]
        if not parents:
            return None
        parents.sort(key=lambda item: (len(item["scope"]["columns"]), item["created_at"]))
        parent = parents[0]
        artifact_path, artifact_hash, row_count = export_csv(self.source_dir, self.artifact_dir, scope)
        if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_hash:
            artifact_path.unlink(missing_ok=True)
            raise RuntimeError("source changed while the reused scope was being generated")
        release = {
            "release_id": uuid.uuid4().hex,
            "request_id": request["request_id"],
            "source_file": scope["file"],
            "purpose_key": request["purpose_key"],
            "scope": scope,
            "artifact_name": artifact_path.name,
            "artifact_sha256": artifact_hash,
            "source_sha256": source_hash,
            "row_count": row_count,
            "parent_release_id": parent["release_id"],
            "created_at": utc_now(),
        }
        try:
            self.store.create_release(release, {
                "reuse": "narrower-scope-from-existing-release",
                "source_release_id": parent["release_id"],
            })
        except Exception:
            artifact_path.unlink(missing_ok=True)
            raise
        result = self._public_release(release)
        result["decision"] = "partial"
        return result

    def record_decision(self, request_id: str, facilitator: dict[str, Any], stakeholder: dict[str, Any]) -> dict[str, Any]:
        request = self.store.get_request(request_id)
        if request is None or request["status"] != "pending":
            raise ValueError("request is missing or no longer pending")
        facilitator = _normalize_decision(facilitator, "facilitator")
        stakeholder = _normalize_decision(stakeholder, "stakeholder")
        decisions = {"facilitator": facilitator, "stakeholder": stakeholder}
        if "refuse" in (facilitator["outcome"], stakeholder["outcome"]):
            self.store.record_terminal_request(request_id, "refused", decisions)
            return {"request_id": request_id, "status": "refused", "release_id": None}
        if "clarify" in (facilitator["outcome"], stakeholder["outcome"]):
            self.store.record_terminal_request(request_id, "clarify", decisions)
            return {"request_id": request_id, "status": "clarify", "release_id": None}

        requested = request["requested_scope"]
        allowed_scope = _intersection(requested, facilitator, stakeholder)
        if allowed_scope is None:
            self.store.record_terminal_request(request_id, "clarify", decisions)
            return {"request_id": request_id, "status": "clarify", "release_id": None, "reason": "decisions have no common allowed scope"}

        original_decisions_complete = all(item["outcome"] == "complete" for item in (facilitator, stakeholder))
        status = "complete" if original_decisions_complete and allowed_scope == requested else "partial"
        purpose_key = request["purpose_key"]
        source_path = (self.source_dir / requested["file"]).resolve()
        try:
            source_path.relative_to(self.source_dir)
        except ValueError as exc:
            raise ValueError("source file escapes configured directory") from exc
        if not source_path.is_file():
            raise FileNotFoundError("source file is unavailable")
        source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        existing = [
            release for release in self.store.all_active_releases(purpose_key, requested["file"])
            if _purpose_key(release["source_safeguards"]) == _purpose_key(request["safeguards"])
            and release["source_sha256"] == source_hash
        ]
        for release in existing:
            if release["scope"] == allowed_scope:
                self.store.record_reuse(request_id, release["release_id"], decisions)
                result = self._public_release(release)
                result.update({"request_id": request_id, "status": "released", "reused": True})
                return result

        parents = [r for r in existing if r["source_sha256"] == source_hash and _scope_covers(r["scope"], allowed_scope)]
        parents.sort(key=lambda item: (len(item["scope"]["columns"]), item["created_at"]))
        parent_id = parents[0]["release_id"] if parents else None
        artifact_path, artifact_hash, row_count = export_csv(self.source_dir, self.artifact_dir, allowed_scope)
        latest_source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if latest_source_hash != source_hash:
            artifact_path.unlink(missing_ok=True)
            raise RuntimeError("source changed while the release was being generated")
        release = {
            "release_id": uuid.uuid4().hex,
            "request_id": request_id,
            "source_file": requested["file"],
            "purpose_key": purpose_key,
            "scope": allowed_scope,
            "artifact_name": artifact_path.name,
            "artifact_sha256": artifact_hash,
            "source_sha256": source_hash,
            "row_count": row_count,
            "parent_release_id": parent_id,
            "created_at": utc_now(),
        }
        try:
            self.store.create_release(release, decisions)
        except Exception:
            artifact_path.unlink(missing_ok=True)
            raise
        result = self._public_release(release)
        result.update({"request_id": request_id, "status": "released", "reused": False, "decision": status})
        return result

    @staticmethod
    def _public_release(release: dict[str, Any]) -> dict[str, Any]:
        return {key: release.get(key) for key in ("release_id", "scope", "artifact_sha256", "source_sha256", "row_count", "parent_release_id", "created_at")}

    def get_request(self, request_id: str) -> dict[str, Any] | None:
        return self.store.get_request(request_id)

    def get_release(self, release_id: str) -> dict[str, Any] | None:
        release = self.store.get_release(release_id)
        if release is None:
            return None
        public = self._public_release(release)
        public.update({"request_id": release["request_id"], "origin_thread_id": release["origin_thread_id"], "requested_by": release["requested_by"], "revoked_at": release["revoked_at"]})
        return public

    def revoke_release(self, release_id: str) -> bool:
        return self.store.revoke_release(release_id)

    def download_path(self, release_id: str) -> Path:
        release = self.store.get_release(release_id)
        if release is None:
            raise FileNotFoundError("release not found")
        if release["revoked_at"]:
            raise PermissionError("release has been revoked")
        path = (self.artifact_dir / release["artifact_name"]).resolve()
        try:
            path.relative_to(self.artifact_dir.resolve())
        except ValueError as exc:
            raise FileNotFoundError("release artifact not found") from exc
        if not path.is_file():
            raise FileNotFoundError("release artifact not found")
        return path
