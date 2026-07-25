"""Collect production traffic evidence for Phase 11.1.4.

The collector reads exported access logs in text, CSV or JSON format and counts
legacy `/api/...` requests separately from Django replacement `/api/v1/...`
requests. It is read-only and never disables routes.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse


API_PATH_PATTERN = re.compile(r"(?P<path>/api(?:/[A-Za-z0-9._~{}-]+)+)")
SECRET_PATTERN = re.compile(
    r"(?i)(token|api_key|apikey|password|secret|authorization|session_id)=([^&\s]+)"
)
CLIENT_MARKERS = (
    "client=",
    "client_id=",
    "client-id=",
    "user-agent",
    "user_agent",
    "ua=",
    "x-forwarded-for",
    "remote_addr",
    "ip=",
)
JSON_PATH_FIELDS = ("path", "url", "uri", "request_uri", "request", "message")
JSON_CLIENT_FIELDS = ("client", "client_id", "user_agent", "remote_addr", "ip", "source")


def is_replacement_api_path(path):
    """Return True when the path belongs to the Django `/api/v1/...` namespace."""
    return path == "/api/v1" or path.startswith("/api/v1/")


def is_legacy_api_path(path):
    """Return True when the path belongs to legacy `/api/...`, excluding `/api/v1/...`."""
    return path.startswith("/api/") and not is_replacement_api_path(path)


def mask_sensitive_text(text):
    """Mask token/password-like values before samples are written to reports."""
    return SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=***", str(text))


def normalize_path(value):
    """Extract a clean API path from a path, URL or HTTP request text."""
    raw_value = str(value or "").strip()
    if not raw_value:
        return None

    match = API_PATH_PATTERN.search(raw_value)
    if not match:
        return None

    path = match.group("path").rstrip(".")
    parsed = urlparse(path)
    return parsed.path or path


def extract_api_paths(text):
    """Extract all API paths from one text record."""
    paths = []
    for match in API_PATH_PATTERN.finditer(str(text or "")):
        path = match.group("path").rstrip(".")
        if path not in {"/api", "/api/"}:
            paths.append(path)
    return paths


def record_has_known_client(record_text, client_value=None):
    """Return True when a traffic record has a visible client identity."""
    if str(client_value or "").strip():
        return True
    lowered = str(record_text or "").lower()
    return any(marker in lowered for marker in CLIENT_MARKERS)


def analyze_records(records, source_name="<memory>"):
    """Analyze normalized traffic records and count legacy/replacement usage."""
    legacy_requests = 0
    replacement_requests = 0
    unknown_clients = 0
    legacy_samples = []
    replacement_samples = []

    for line_number, record in enumerate(records, start=1):
        text = str(record.get("text") or "")
        client = record.get("client")
        paths = record.get("paths") or extract_api_paths(text)

        for path in paths:
            sample = {
                "source": source_name,
                "line": line_number,
                "path": path,
                "sample": mask_sensitive_text(text)[:300],
            }
            if is_replacement_api_path(path):
                replacement_requests += 1
                if len(replacement_samples) < 10:
                    replacement_samples.append(sample)
            elif is_legacy_api_path(path):
                legacy_requests += 1
                if not record_has_known_client(text, client):
                    unknown_clients += 1
                if len(legacy_samples) < 10:
                    legacy_samples.append(sample)

    return {
        "source": source_name,
        "records_checked": len(records),
        "legacy_requests": legacy_requests,
        "replacement_requests": replacement_requests,
        "unknown_clients": unknown_clients,
        "legacy_samples": legacy_samples,
        "replacement_samples": replacement_samples,
    }


def read_text_records(path):
    """Read plain text access logs as one record per line."""
    with Path(path).open("r", encoding="utf-8", errors="ignore") as file:
        return [{"text": line.rstrip("\n")} for line in file]


def read_csv_records(path):
    """Read CSV logs and inspect common path/client columns."""
    records = []
    with Path(path).open("r", encoding="utf-8", errors="ignore", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            return records
        for row in reader:
            values = [str(value or "") for value in row.values()]
            text = " ".join(values)
            client = next((row.get(field) for field in JSON_CLIENT_FIELDS if row.get(field)), None)
            explicit_paths = [
                normalize_path(row.get(field))
                for field in JSON_PATH_FIELDS
                if row.get(field)
            ]
            paths = [path for path in explicit_paths if path]
            if not paths:
                paths = extract_api_paths(text)
            records.append({"text": text, "paths": paths, "client": client})
    return records


def iter_json_items(raw_text):
    """Yield JSON objects from JSON array/object files or newline-delimited JSON."""
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
    """Read JSON or JSONL logs and inspect path/client fields."""
    raw_text = Path(path).read_text(encoding="utf-8", errors="ignore")
    records = []
    for item in iter_json_items(raw_text):
        if not isinstance(item, dict):
            item = {"message": item}
        values = [str(value or "") for value in item.values()]
        text = " ".join(values)
        client = next((item.get(field) for field in JSON_CLIENT_FIELDS if item.get(field)), None)
        explicit_paths = [
            normalize_path(item.get(field))
            for field in JSON_PATH_FIELDS
            if item.get(field)
        ]
        paths = [path for path in explicit_paths if path]
        if not paths:
            paths = extract_api_paths(text)
        records.append({"text": text, "paths": paths, "client": client})
    return records


def read_log_records(path):
    """Read a log file based on its extension."""
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return read_csv_records(path)
    if suffix in {".json", ".jsonl", ".ndjson"}:
        return read_json_records(path)
    return read_text_records(path)


def analyze_log_file(path):
    """Analyze one production evidence file."""
    log_path = Path(path)
    if not log_path.exists():
        return {
            "source": str(log_path),
            "exists": False,
            "records_checked": 0,
            "legacy_requests": 0,
            "replacement_requests": 0,
            "unknown_clients": 0,
            "legacy_samples": [],
            "replacement_samples": [],
            "errors": ["Evidence file does not exist."],
        }

    records = read_log_records(log_path)
    result = analyze_records(records, source_name=str(log_path))
    result["exists"] = True
    result["errors"] = []
    return result


def parse_log_paths(values=None, env=None):
    """Read evidence file paths from CLI values or `PHASE11_1_4_LOG_PATHS`."""
    if values:
        return [str(Path(value)) for value in values]

    env = env or os.environ
    raw = env.get("PHASE11_1_4_LOG_PATHS", "")
    if not raw.strip():
        return []
    return [part.strip() for part in re.split(r"[;,]", raw) if part.strip()]


def evaluate_traffic_evidence(log_paths=None, period=None, env=None):
    """Evaluate whether production evidence supports decommission."""
    started_at = time.perf_counter()
    env = env or os.environ
    paths = parse_log_paths(log_paths, env=env)
    period_value = period or env.get("PHASE11_1_4_PERIOD") or "NOT_PROVIDED"
    source_results = [analyze_log_file(path) for path in paths]

    legacy_requests = sum(item["legacy_requests"] for item in source_results)
    replacement_requests = sum(item["replacement_requests"] for item in source_results)
    unknown_clients = sum(item["unknown_clients"] for item in source_results)
    records_checked = sum(item["records_checked"] for item in source_results)
    logs_checked = sum(1 for item in source_results if item.get("exists"))
    errors = [error for item in source_results for error in item.get("errors", [])]

    if not paths:
        errors.append("No production evidence files were provided.")
    if legacy_requests:
        errors.append("Legacy API requests were detected.")
    if unknown_clients:
        errors.append("Unknown legacy API clients were detected.")
    if logs_checked and replacement_requests == 0:
        errors.append("No Django `/api/v1/...` replacement traffic was observed.")

    safe_to_decommission = bool(paths) and logs_checked == len(paths) and not errors
    return {
        "status": "READY_FOR_DECOMMISSION" if safe_to_decommission else "BLOCKED_SAFELY",
        "period": period_value,
        "legacy_requests": legacy_requests,
        "replacement_requests": replacement_requests,
        "unknown_clients": unknown_clients,
        "records_checked": records_checked,
        "logs_provided": bool(paths),
        "logs_checked": logs_checked,
        "safe_to_decommission": safe_to_decommission,
        "decision": "READY_FOR_DECOMMISSION" if safe_to_decommission else "KEEP_LEGACY_API_ACTIVE",
        "sources": source_results,
        "security": {
            "credentials_masked": True,
            "logs_treated_read_only": True,
            "raw_logs_removed_from_report": True,
        },
        "errors": errors,
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }


def main():
    """Command line entrypoint for evidence collection."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.4 production traffic evidence collector")
    parser.add_argument("--log", action="append", default=[], help="Path to text, CSV, JSON or JSONL log export.")
    parser.add_argument("--period", default=None, help="Verification period, for example 2026-01-01_to_2026-01-30.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when evidence is blocked. Default keeps blocked state as exit 0.",
    )
    args = parser.parse_args()
    result = evaluate_traffic_evidence(log_paths=args.log, period=args.period)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["safe_to_decommission"]:
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
