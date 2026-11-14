# Case Atlas Release Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a local service that records data-release negotiations and publishes only deterministic CSV scopes allowed by both role-play decisions.

**Architecture:** A Python 3.12 standard-library HTTP service reads facilitator CSVs from a read-only source directory, stores requests/releases in SQLite, and writes immutable release artifacts to persistent storage. AnythingLLM integration remains a private service-client concern; deployment must put team authentication in front of downloads and must not mount facilitator files into AnythingLLM.

**Tech Stack:** Python 3.12, `http.server`, `sqlite3`, `csv`, `hashlib`, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-14-case-atlas-data-release-design.md`

## Global Constraints

- Never mount `99_Facilitador/` into the consultant AnythingLLM container.
- Never alter original CSVs; export filtered copies only.
- Accept only catalogued files and columns; never accept arbitrary paths or SQL.
- Facilitator and stakeholder must both permit a release; disagreement or missing context produces clarification, and either refusal blocks publication.
- Release links have no automatic expiry, are team-authenticated at deployment, and can be explicitly revoked.
- A release is associated with the original chat reference; do not trust a model-invented thread ID as verified metadata.
- Invalid decisions, model/service errors, and storage failures fail closed.

## Review Focus

- Unknown CSV names, columns, traversal strings, and arbitrary filters: reject before reading any source file.
- Facilitator/stakeholder refusal or disagreement: record decision, create no artifact.
- Partial decision scopes: publish only the intersection of allowed columns and periods.
- Repeated identical requests and narrowed reuse: reuse or derive without exposing broader data.
- Missing source files, invalid dates, and revoked releases: return a safe error without changing source data or serving bytes.

---

### Task 1: Scope validation and deterministic CSV export

**Files:**
- Create: `release_service/catalog.py`
- Create: `release_service/exporter.py`
- Test: `tests/test_exporter.py`

**Interfaces:**
- `catalog.py` exposes the catalog of source CSV names and their permitted columns/date fields.
- `exporter.py` exposes `export_csv(source_dir, artifact_dir, scope) -> (artifact_path, sha256, row_count)`; scope contains an allowlisted filename, requested columns, and optional ISO date bounds.

- [x] Write tests for accepted subset export, date boundaries, empty results, unknown columns/files, path traversal, and invalid dates.
- [x] Run those tests and confirm they fail because the service is not implemented.
- [x] Implement the catalog and CSV exporter with streaming reads and UTF-8 BOM support.
- [x] Run the exporter tests and confirm they pass.

### Task 2: Durable requests, consensus decisions, releases, and reuse

**Files:**
- Create: `release_service/store.py`
- Create: `release_service/service.py`
- Test: `tests/test_release_service.py`

**Interfaces:**
- `store.py` owns SQLite schema and operations for requests/releases.
- `service.py` exposes `submit_request(payload)`, `record_decision(request_id, facilitator, stakeholder)`, `get_release(release_id)`, `revoke_release(release_id)`, and `download_path(release_id)`.
- Decision scope is intersected deterministically. `clarify` or `refuse` never creates a release. Identical purpose/scope reuses an existing active artifact; narrower scope creates a derivative with parent release metadata.

- [x] Write tests for required origin reference, both-party consensus, refusal, clarification, partial scope intersection, idempotent reuse, narrower derivatives, provenance/hash persistence, and revocation.
- [x] Run those tests and confirm they fail because the service is not implemented.
- [x] Implement SQLite persistence and the release state machine, invoking Task 1 only after consensus validation.
- [x] Run the release-service tests and confirm they pass.

### Task 3: Private HTTP API and download route

**Files:**
- Create: `release_service/http_api.py`
- Create: `release_service/__main__.py`
- Test: `tests/test_http_api.py`

**Interfaces:**
- Environment: `CASE_RELEASE_SOURCE_DIR`, `CASE_RELEASE_STORAGE_DIR`, `CASE_RELEASE_API_TOKEN`, `CASE_RELEASE_HOST`, `CASE_RELEASE_PORT`.
- `POST /v1/requests` creates a request; `POST /v1/requests/{id}/decision` records structured decisions; `GET /v1/requests/{id}` returns status; `GET /v1/releases/{id}/download` streams an active artifact as attachment; `POST /v1/releases/{id}/revoke` revokes it.
- API mutations require bearer token. The service binds to loopback by default. The download route is only safe to expose through an authenticated team gateway; it must not be published as an unauthenticated public endpoint.

- [x] Write tests for auth, JSON validation, status/download response, attachment headers, and revoked/unknown IDs.
- [x] Run those tests and confirm they fail because the API is not implemented.
- [x] Implement the standard-library HTTP server with bounded request bodies and safe error responses.
- [x] Run the API tests and confirm they pass.

### Task 4: Local operator documentation and deployment boundary

**Files:**
- Create: `Dockerfile.release`
- Create: `compose.release.yml`
- Create: `release_service/README.md`
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-11-14-case-atlas-data-release-design.md`

- [x] Document local run/configuration, backup of SQLite and artifacts, API examples, Caddy team-auth boundary, and the fact that download authentication and trusted AnythingLLM thread-ID capture must be validated before public deployment.
- [x] Update the project architecture flow to show the private release service and explicitly preserve the no-mount boundary.
- [x] Run `python3 -m unittest discover -s tests -v` and `git diff --check`; record any environment limitation.
- [x] Review changed files and confirm existing uncommitted files outside this plan's scope remain untouched.

### Task 5: AnythingLLM custom skill with trusted conversation metadata

**Files:**
- Create: `release_service/decision_context.py`
- Modify: `release_service/service.py`
- Modify: `release_service/http_api.py`
- Create: `anythingllm/agent-skills/case-atlas-release/plugin.json`
- Create: `anythingllm/agent-skills/case-atlas-release/handler.js`
- Test: `tests/test_decision_context.py`
- Test: `anythingllm/agent-skills/case-atlas-release/handler.test.js`

**Interfaces:**
- `POST /v1/decision-context` (API bearer token) accepts a catalogued `stakeholder_id` and returns only the general release policy plus that persona's entry/profile; it never returns source CSV rows.
- The skill obtains `workspace.name`, `user_id`, and `trackedChatId` from AnythingLLM's server runtime context. It fails closed if the workspace is not Case Atlas or any identity/chat value is absent; those values are never tool parameters.
- The skill uses the active AnythingLLM provider instance to run separate facilitator and stakeholder evaluations, passes their JSON decisions to the existing decision API, and returns only the decision, request/release ID, and stable download URL.

- [x] Write RED tests for persona context isolation and authenticated context API.
- [x] Implement selected-persona context extraction and the context endpoint.
- [x] Write RED Node tests for trusted runtime metadata, invalid/missing context, successful role-play calls, release URL construction, and fail-closed errors.
- [x] Implement the custom skill and test it without installing or activating it in production.
- [x] Add the skill installation path and live-runtime validation steps to `release_service/README.md`.
- [x] Run Python tests, Node tests, Compose validation, and `git diff --check`.
