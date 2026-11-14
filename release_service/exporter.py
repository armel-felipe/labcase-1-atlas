"""Create deterministic, filtered copies of allowlisted source CSVs."""

import csv
import hashlib
import os
import re
import uuid
from datetime import date
from pathlib import Path
from typing import Any

from .catalog import CATALOG

MAX_RELEASE_ROWS = 100_000
_SAFE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_bound(value: Any, name: str) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str) or not _SAFE_DATE.fullmatch(value):
        raise ValueError(f"{name} must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid date") from exc


def export_csv(source_dir: Path, artifact_dir: Path, scope: dict[str, Any]) -> tuple[Path, str, int]:
    """Export an allowlisted subset and return its path, SHA-256, and row count."""
    filename = scope.get("file")
    if not isinstance(filename, str) or filename not in CATALOG:
        raise ValueError("file is not in the release catalog")
    source = CATALOG[filename]

    columns = scope.get("columns")
    if not isinstance(columns, list) or not columns or any(not isinstance(col, str) for col in columns):
        raise ValueError("columns must be a non-empty list")
    if len(columns) != len(set(columns)) or any(col not in source.columns for col in columns):
        raise ValueError("columns contain duplicates or unapproved fields")
    # Keep catalog order so equivalent scopes always produce byte-identical CSVs.
    columns = [col for col in source.columns if col in columns]

    lower = _parse_bound(scope.get("date_from"), "date_from")
    upper = _parse_bound(scope.get("date_to"), "date_to")
    if lower and upper and lower > upper:
        raise ValueError("date_from must be on or before date_to")
    if (lower or upper) and not source.date_column:
        raise ValueError("date filtering is not supported for this source")

    root = Path(source_dir).resolve()
    source_path = (root / filename).resolve()
    try:
        source_path.relative_to(root)
    except ValueError as exc:
        raise ValueError("source path escapes configured directory") from exc
    if not source_path.is_file():
        raise ValueError("source file is unavailable")

    artifact_root = Path(artifact_dir).resolve()
    artifact_root.mkdir(parents=True, exist_ok=True)
    destination = artifact_root / f"{uuid.uuid4().hex}.csv"
    temporary = artifact_root / f".{destination.name}.tmp"
    count = 0
    try:
        with source_path.open("r", encoding="utf-8-sig", newline="") as source_handle:
            reader = csv.DictReader(source_handle)
            headers = reader.fieldnames or []
            if len(headers) != len(set(headers)) or any(col not in headers for col in columns):
                raise ValueError("source CSV schema does not match the release scope")
            if source.date_column and (lower or upper) and source.date_column not in headers:
                raise ValueError("source CSV is missing its catalogued date field")
            with temporary.open("w", encoding="utf-8-sig", newline="") as artifact_handle:
                writer = csv.DictWriter(artifact_handle, fieldnames=columns, extrasaction="raise", lineterminator="\n")
                writer.writeheader()
                for row in reader:
                    if lower or upper:
                        raw_date = (row.get(source.date_column or "") or "")[:10]
                        try:
                            row_date = date.fromisoformat(raw_date)
                        except ValueError as exc:
                            raise ValueError("source row has an invalid catalogued date") from exc
                        if lower and row_date < lower or upper and row_date > upper:
                            continue
                    writer.writerow({col: row.get(col, "") for col in columns})
                    count += 1
                    if count > MAX_RELEASE_ROWS:
                        raise ValueError(f"release exceeds the {MAX_RELEASE_ROWS} row limit")
        os.replace(temporary, destination)
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        return destination, digest, count
    except Exception:
        temporary.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        raise
