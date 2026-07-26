"""Load and validate real production traffic evidence for Phase 11.1.5.4.

The loader accepts CSV, JSON/JSONL and text log files. It counts legacy
`/api/...` traffic separately from Django `/api/v1/...` traffic and writes a
JSON report. It never changes routes, proxy config, database state or legacy
code.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "reports"
    / "REAL_PRODUCTION_TRAFFIC_REPORT.json"
)

API_PATH_PATTERN = re.compile(r"(?P<path>/api(?:/[A-Za-z0-9._~{}-]+)+)")
STATUS_PATTERN = re.compile(r"\s(?P<status>[1-5][0-9]{2})(?:\s|$)")
CLIENT_MARKERS = ("client=", "client_id=", "user-agent", "user_agent", "ua=", "source=", "ip=")
PATH_FIELDS = ("endpoint", "path", "url", "uri", "request_uri", "request", "message")
CLIENT_FIELDS = ("client", "client_id", "user_agent", "source", "ip", "remote_addr")
STATUS_FIELDS = ("status_code", "status", "http_status")
COUNT_FIELDS = ("request_count", "count", "requests")


def is_replacement_path(path):
    """Return True for Django `/api/v1/...` paths."""
    return path == "/api/v1" or path.startswith("/api/v1/")


def is_legacy_path(path):
    """Return True for legacy `/api/...` paths, excluding `/api/v1/...`."""
    return path.startswith("/api/") and not is_replacement_path(path)


def extract_paths(text):
    """Extract API paths from a log-like text value."""
    paths = []
    for match in API_PATH_PATTERN.finditer(str(text or "")):
        path = urlparse(match.group("path").rstrip(".")).path
        if path not in {"/api", "/api/"}:
            paths.append(path)
    return paths


def extract_status(text):
    """Extract HTTP status code from text when possible."""
    match = STATUS_PATTERN.search(f" {text} ")
    if not match:
        return None
    return int(match.group("status"))


def has_known_client(text, client=None):
    """Return True when client identity is present."""
    if str(client or "").strip():
        return True
    lowered = str(text or "").lower()
    return any(marker in lowered for marker in CLIENT_MARKERS)


def int_value(value, default=1):
    """Parse integer values from logs; default one request per record."""
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default


def normalize_record(data):
    """Normalize dict-like data into paths, status, count and client fields."""
    values = [str(value or "") for value in data.values()]
    text = " ".join(values)
    paths = []
    for field in PATH_FIELDS:
        if data.get(field):
            paths.extend(extract_paths(data[field]))
    if not paths:
        paths = extract_paths(text)
    client = next((data.get(field) for field in CLIENT_FIELDS if data.get(field)), None)
    status_value = next((data.get(field) for field in STATUS_FIELDS if data.get(field)), None)
    count_value = next((data.get(field) for field in COUNT_FIELDS if data.get(field)), None)
    return {
        "text": text,
        "paths": paths,
        "client": client,
        "status_code": int_value(status_value, default=extract_status(text) or 0),
        "request_count": int_value(count_value, default=1),
    }


def read_text_records(path):
    """Read plain text logs."""
    records = []
    with Path(path).open("r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            text = line.rstrip("\n")
            records.append(
                {
                    "text": text,
                    "paths": extract_paths(text),
                    "client": None,
                    "status_code": extract_status(text) or 0,
                    "request_count": 1,
                }
            )
    return records


def read_csv_records(path):
    """Read CSV exports."""
    with Path(path).open("r", encoding="utf-8", errors="ignore", newline="") as file:
        return [normalize_record(row) for row in csv.DictReader(file)]


def iter_json_items(raw_text):
    """Yield objects from JSON array, JSON object or JSONL data."""
    stripped = raw_text.strip()
    if not stripped:
        return
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        for line in stripped.splitlines():
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
    """Read JSON or JSONL exports."""
    raw_text = Path(path).read_text(encoding="utf-8", errors="ignore")
    records = []
    for item in iter_json_items(raw_text):
        if not isinstance(item, dict):
            item = {"message": item}
        records.append(normalize_record(item))
    return records


def read_records(path):
    """Read records from supported input type."""
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return read_csv_records(path)
    if suffix in {".json", ".jsonl", ".ndjson"}:
        return read_json_records(path)
    return read_text_records(path)


def analyze_records(records):
    """Analyze normalized production records."""
    legacy_requests = 0
    django_requests = 0
    unknown_clients = 0
    total_requests = 0
    error_requests = 0
    client_names = set()

    for record in records:
        count = int_value(record.get("request_count"), default=1)
        status_code = int_value(record.get("status_code"), default=0)
        paths = record.get("paths") or []
        if status_code >= 400:
            error_requests += count
        for path in paths:
            total_requests += count
            if record.get("client"):
                client_names.add(str(record["client"]))
            if is_replacement_path(path):
                django_requests += count
            elif is_legacy_path(path):
                legacy_requests += count
                if not has_known_client(record.get("text"), record.get("client")):
                    unknown_clients += count

    error_rate = round(error_requests / total_requests, 6) if total_requests else 0
    return {
        "legacy_requests": legacy_requests,
        "django_requests": django_requests,
        "unknown_clients": unknown_clients,
        "total_api_requests": total_requests,
        "error_requests": error_requests,
        "error_rate": error_rate,
        "known_clients": sorted(client_names),
    }


def parse_input_paths(values=None, env=None):
    """Read input paths from CLI or `PHASE11_1_5_4_INPUTS`."""
    if values:
        return values
    env = env or os.environ
    raw = env.get("PHASE11_1_5_4_INPUTS", "")
    if not raw.strip():
        return []
    return [part.strip() for part in re.split(r"[;,]", raw) if part.strip()]


def collect_production_evidence(input_paths=None, period=None, report_path=None, env=None):
    """Collect production evidence and write the report JSON."""
    paths = parse_input_paths(input_paths, env=env)
    all_records = []
    errors = []
    sources = []

    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            errors.append(f"Input file does not exist: {path}.")
            continue
        records = read_records(path)
        all_records.extend(records)
        sources.append({"path": str(path), "records": len(records)})

    analysis = analyze_records(all_records)
    if not paths:
        errors.append("No real production data inputs were provided.")
    if analysis["legacy_requests"] != 0:
        errors.append("Legacy API traffic was detected.")
    if analysis["django_requests"] <= 0:
        errors.append("Django `/api/v1/...` traffic was not observed.")
    if analysis["unknown_clients"] != 0:
        errors.append("Unknown clients were detected.")

    ready = bool(paths) and not errors
    result = {
        "status": "COMPLETE_EVIDENCE_PACKAGE" if ready else "INCOMPLETE_EVIDENCE_PACKAGE",
        "ready_for_shutdown": ready,
        "period": period or "NOT_PROVIDED",
        "data_sources": sources,
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
        "database_archived": False,
        "legacy_code_removed": False,
        "errors": errors,
    }

    output_path = Path(report_path or DEFAULT_REPORT_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Phase 11.1.5.4 production evidence loader")
    parser.add_argument("--input", action="append", default=[], help="CSV, JSON, JSONL or text log input.")
    parser.add_argument("--period", default=None, help="Collection period label.")
    parser.add_argument("--report", default=None, help="Report output path.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when evidence is incomplete.")
    args = parser.parse_args()
    result = collect_production_evidence(args.input, period=args.period, report_path=args.report)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["ready_for_shutdown"]:
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
