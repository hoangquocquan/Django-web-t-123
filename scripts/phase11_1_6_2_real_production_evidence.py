"""Validate real production API migration evidence for Phase 11.1.6.2.

This workflow reads evidence files from `docs/migration/production_evidence/input`.
It supports IIS W3C logs, CSV exports, JSON/JSONL logs and generic API gateway
text logs. It only analyzes logs and writes a report. It does not disable
Legacy API, modify IIS, change proxy rules, change routes or execute shutdown.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = PROJECT_ROOT / "docs" / "migration" / "production_evidence" / "input"
DEFAULT_REPORT_PATH = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "reports"
    / "REAL_PRODUCTION_EVIDENCE_REPORT.json"
)

SUPPORTED_SUFFIXES = {".csv", ".json", ".jsonl", ".ndjson", ".log", ".txt"}
API_PATH_PATTERN = re.compile(r"(?P<path>/api(?:/[A-Za-z0-9._~{}-]+)*)")
STATUS_PATTERN = re.compile(r"(?:\s|status=|status_code=)(?P<status>[1-5][0-9]{2})(?:\s|$)")
PATH_FIELDS = ("endpoint", "path", "url", "uri", "request_uri", "cs-uri-stem", "message", "request")
CLIENT_FIELDS = ("client", "client_id", "ip", "remote_addr", "c-ip", "source")
STATUS_FIELDS = ("status_code", "status", "http_status", "sc-status")
TIME_FIELDS = ("timestamp", "time", "datetime", "date")


def is_replacement_path(path):
    """Return True for Django replacement `/api/v1/*` paths."""
    return path == "/api/v1" or path.startswith("/api/v1/")


def is_legacy_path(path):
    """Return True for legacy `/api/*` paths excluding `/api/v1/*`."""
    return path.startswith("/api/") and not is_replacement_path(path)


def extract_paths(text):
    """Extract API paths from free-form text."""
    paths = []
    for match in API_PATH_PATTERN.finditer(str(text or "")):
        parsed = urlparse(match.group("path").rstrip(".,;")).path
        if parsed not in {"/api", "/api/"}:
            paths.append(parsed)
    return paths


def extract_status(text):
    """Extract HTTP status code from text when available."""
    match = STATUS_PATTERN.search(f" {text} ")
    return int(match.group("status")) if match else 0


def int_value(value, default=0):
    """Parse integer values safely."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def normalize_client(value):
    """Normalize client identity and treat blank placeholders as unknown."""
    client = str(value or "").strip()
    if client.lower() in {"", "-", "unknown", "null", "none"}:
        return None
    return client


def normalize_record(data, source):
    """Normalize a dict-like log record into the evidence shape."""
    values = [str(value or "") for value in data.values()]
    combined = " ".join(values)

    paths = []
    for field in PATH_FIELDS:
        if data.get(field):
            paths.extend(extract_paths(data[field]))
    if not paths:
        paths = extract_paths(combined)

    client = None
    for field in CLIENT_FIELDS:
        if data.get(field):
            client = normalize_client(data[field])
            break

    status = 0
    for field in STATUS_FIELDS:
        if data.get(field):
            status = int_value(data[field], default=0)
            break
    if not status:
        status = extract_status(combined)

    timestamp = ""
    for field in TIME_FIELDS:
        if data.get(field):
            timestamp = str(data[field]).strip()
            break

    return {
        "source": str(source),
        "timestamp": timestamp,
        "paths": paths,
        "client": client,
        "status_code": status,
        "raw": combined,
    }


def read_csv_records(path):
    """Read CSV evidence exports."""
    with Path(path).open("r", encoding="utf-8", errors="ignore", newline="") as file:
        return [normalize_record(row, path) for row in csv.DictReader(file)]


def iter_json_items(raw_text):
    """Yield JSON objects from JSON array, JSON object or JSONL content."""
    stripped = raw_text.strip()
    if not stripped:
        return
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        for line in stripped.splitlines():
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"message": line}
        return
    if isinstance(parsed, list):
        for item in parsed:
            yield item
    elif isinstance(parsed, dict):
        yield parsed
    else:
        yield {"message": parsed}


def read_json_records(path):
    """Read JSON, JSONL and API gateway JSON exports."""
    raw_text = Path(path).read_text(encoding="utf-8", errors="ignore")
    records = []
    for item in iter_json_items(raw_text):
        if not isinstance(item, dict):
            item = {"message": item}
        records.append(normalize_record(item, path))
    return records


def parse_iis_fields(lines):
    """Read IIS W3C `#Fields:` definition."""
    for line in lines:
        if line.startswith("#Fields:"):
            return line.replace("#Fields:", "", 1).strip().split()
    return []


def read_text_or_iis_records(path):
    """Read IIS W3C logs or generic text/API gateway logs."""
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    fields = parse_iis_fields(lines)
    records = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if fields:
            values = stripped.split()
            row = {field: values[index] if index < len(values) else "" for index, field in enumerate(fields)}
            if row.get("date") and row.get("time"):
                row["timestamp"] = f"{row['date']}T{row['time']}Z"
            records.append(normalize_record(row, path))
        else:
            records.append(normalize_record({"message": stripped}, path))

    return records


def read_records(path):
    """Read one supported evidence file."""
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return read_csv_records(path)
    if suffix in {".json", ".jsonl", ".ndjson"}:
        return read_json_records(path)
    return read_text_or_iis_records(path)


def discover_input_files(input_dir=None):
    """Discover supported evidence files in the input directory."""
    directory = Path(input_dir or DEFAULT_INPUT_DIR)
    if not directory.exists():
        return []
    return sorted(path for path in directory.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES)


def infer_collection_period(records, explicit_period=None):
    """Infer a readable collection period from record timestamps."""
    if explicit_period:
        return explicit_period
    timestamps = sorted(record["timestamp"] for record in records if record.get("timestamp"))
    if not timestamps:
        return "NOT_PROVIDED"
    return f"{timestamps[0]} - {timestamps[-1]}"


def analyze_records(records):
    """Count Legacy API, Django API and unknown-client traffic."""
    legacy_requests = 0
    django_requests = 0
    unknown_clients = 0
    total_api_requests = 0
    error_requests = 0
    known_clients = set()

    for record in records:
        paths = record.get("paths") or []
        if not paths:
            continue
        if record.get("status_code", 0) >= 400:
            error_requests += 1
        if record.get("client"):
            known_clients.add(record["client"])

        for path in paths:
            if is_legacy_path(path) or is_replacement_path(path):
                total_api_requests += 1
                if not record.get("client"):
                    unknown_clients += 1
            if is_legacy_path(path):
                legacy_requests += 1
            elif is_replacement_path(path):
                django_requests += 1

    error_rate = round(error_requests / total_api_requests, 6) if total_api_requests else 0
    return {
        "legacy_requests": legacy_requests,
        "django_requests": django_requests,
        "unknown_clients": unknown_clients,
        "total_api_requests": total_api_requests,
        "error_requests": error_requests,
        "error_rate": error_rate,
        "known_clients": sorted(known_clients),
    }


def validate_real_production_evidence(input_dir=None, output_path=None, period=None):
    """Read input evidence and write `REAL_PRODUCTION_EVIDENCE_REPORT.json`."""
    started_at = time.perf_counter()
    files = discover_input_files(input_dir)
    all_records = []
    data_sources = []
    errors = []

    for path in files:
        try:
            records = read_records(path)
        except OSError as exc:
            errors.append(f"Cannot read evidence file {path}: {exc}.")
            records = []
        all_records.extend(records)
        data_sources.append({"path": str(path), "records": len(records), "type": path.suffix.lower().lstrip(".")})

    analysis = analyze_records(all_records)

    if not files:
        errors.append("No production evidence files were found.")
    if not all_records:
        errors.append("No evidence records were found.")
    if analysis["legacy_requests"] != 0:
        errors.append("Legacy `/api/*` traffic was detected.")
    if analysis["django_requests"] <= 0:
        errors.append("Django `/api/v1/*` traffic was not confirmed.")
    if analysis["unknown_clients"] != 0:
        errors.append("Unknown API clients were detected.")

    complete = bool(files) and bool(all_records) and not errors
    report = {
        "status": "COMPLETE_EVIDENCE_PACKAGE" if complete else "INCOMPLETE_EVIDENCE_PACKAGE",
        "ready_for_shutdown": complete,
        "collection_period": infer_collection_period(all_records, explicit_period=period),
        "data_sources": data_sources,
        "legacy_requests": analysis["legacy_requests"],
        "django_requests": analysis["django_requests"],
        "unknown_clients": analysis["unknown_clients"],
        "total_api_requests": analysis["total_api_requests"],
        "error_requests": analysis["error_requests"],
        "error_rate": analysis["error_rate"],
        "known_clients": analysis["known_clients"],
        "legacy_routes_disabled": False,
        "routes_changed": False,
        "proxy_modified": False,
        "iis_modified": False,
        "database_modified": False,
        "shutdown_executed": False,
        "errors": errors,
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    destination = Path(output_path or DEFAULT_REPORT_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.6.2 real production evidence validator")
    parser.add_argument("--input-dir", default=None, help="Evidence input directory.")
    parser.add_argument("--output", default=None, help="Evidence report output path.")
    parser.add_argument("--period", default=None, help="Collection period label.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when evidence is incomplete. Default incomplete state exits 0.",
    )
    args = parser.parse_args()
    result = validate_real_production_evidence(
        input_dir=args.input_dir,
        output_path=args.output,
        period=args.period,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "COMPLETE_EVIDENCE_PACKAGE":
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
