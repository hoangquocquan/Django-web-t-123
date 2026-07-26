"""Phase 11.1.6.5.2 production IIS evidence acceptance validator.

Script nay chi kiem tra goi evidence da duoc ban giao. No khong shutdown
Legacy API, khong sua IIS, khong sua proxy, khong sua route va khong sua
database.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.phase11_1_6_2_real_production_evidence import analyze_records, read_records
except ModuleNotFoundError:
    from phase11_1_6_2_real_production_evidence import analyze_records, read_records


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE_DIR = PROJECT_ROOT / "docs" / "migration" / "production_evidence"
DEFAULT_INPUT_DIR = DEFAULT_PACKAGE_DIR / "input"
DEFAULT_LOG_DIR = DEFAULT_INPUT_DIR / "iis_logs"
DEFAULT_CSV_PATH = DEFAULT_INPUT_DIR / "iis_api_evidence.csv"
DEFAULT_METADATA_PATH = DEFAULT_PACKAGE_DIR / "handover" / "collection_metadata.json"
DEFAULT_STATUS_PATH = DEFAULT_PACKAGE_DIR / "handover" / "EVIDENCE_ACCEPTANCE_STATUS.json"
DEFAULT_REVIEW_PATH = PROJECT_ROOT / "docs" / "reviews" / "PHASE_11.1.6.5.2_EVIDENCE_HANDOVER_REVIEW.md"

REQUIRED_METADATA_FIELDS = [
    "server",
    "environment",
    "iis_site",
    "site_id",
    "collection_start",
    "collection_end",
    "operator",
    "reviewer",
    "notes",
]
REQUIRED_IIS_FIELDS = ["date", "time", "c-ip", "cs-uri-stem", "sc-status", "cs(User-Agent)"]
REQUIRED_CSV_FIELDS = ["timestamp", "source", "client", "endpoint", "status_code", "user_agent"]


def meaningful(value):
    """Tra ve True khi gia tri khong phai placeholder."""
    return str(value or "").strip().lower() not in {"", "pending", "tbd", "missing", "not_provided", "not provided"}


def load_metadata(path=None):
    """Doc metadata ban giao production evidence."""
    metadata_path = Path(path or DEFAULT_METADATA_PATH)
    if not metadata_path.exists():
        return {}, [f"Collection metadata does not exist: {metadata_path}."]
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"Collection metadata is invalid JSON: {exc}."]
    if not isinstance(metadata, dict):
        return {}, ["Collection metadata must be a JSON object."]
    return metadata, []


def validate_metadata(path=None):
    """Kiem tra metadata co du thong tin nguon, period va nguoi phu trach."""
    metadata, errors = load_metadata(path)
    for field in REQUIRED_METADATA_FIELDS:
        if field not in metadata:
            errors.append(f"Metadata field is missing: {field}.")
        elif field != "notes" and not meaningful(metadata.get(field)):
            errors.append(f"Metadata field is pending: {field}.")
    if not meaningful(metadata.get("collection_start")) or not meaningful(metadata.get("collection_end")):
        errors.append("Collection period is not complete.")
    return {"metadata": metadata, "errors": errors}


def discover_iis_logs(log_dir=None):
    """Tim raw IIS W3C logs."""
    directory = Path(log_dir or DEFAULT_LOG_DIR)
    if not directory.exists():
        return []
    return sorted({path for path in directory.rglob("u_ex*.log") if path.is_file()} | {path for path in directory.rglob("*.log") if path.is_file()})


def parse_w3c_fields(path):
    """Doc dong #Fields tu IIS W3C log."""
    for line in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if stripped.startswith("#Fields:"):
            return stripped.replace("#Fields:", "", 1).strip().split()
    return []


def validate_iis_logs(log_dir=None):
    """Kiem tra IIS logs co ton tai va co du W3C fields bat buoc."""
    logs = discover_iis_logs(log_dir)
    errors = []
    reports = []
    if not logs:
        errors.append("IIS logs do not exist.")
    for path in logs:
        fields = parse_w3c_fields(path)
        missing = [field for field in REQUIRED_IIS_FIELDS if field not in fields]
        if missing:
            errors.append(f"IIS log is missing required fields: {path}: {', '.join(missing)}.")
        reports.append({"path": str(path), "fields": fields, "missing_fields": missing})
    return {"logs": reports, "count": len(logs), "errors": errors}


def csv_info(path=None):
    """Kiem tra CSV evidence co ton tai, co du cot va co dong du lieu."""
    csv_path = Path(path or DEFAULT_CSV_PATH)
    if not csv_path.exists():
        return {
            "path": str(csv_path),
            "exists": False,
            "fields": [],
            "rows": 0,
            "records": [],
            "errors": [f"CSV evidence does not exist: {csv_path}."],
        }
    with csv_path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as file:
        reader = csv.DictReader(file)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    missing = [field for field in REQUIRED_CSV_FIELDS if field not in fields]
    errors = []
    if missing:
        errors.append(f"CSV evidence is missing required fields: {', '.join(missing)}.")
    if not rows:
        errors.append("CSV evidence is empty.")
    records = read_records(csv_path) if not missing else []
    return {
        "path": str(csv_path),
        "exists": True,
        "fields": fields,
        "rows": len(rows),
        "records": records,
        "errors": errors,
    }


def evaluate_acceptance(package_dir=None, output_path=None, review_path=None):
    """Danh gia evidence package va ghi JSON/Markdown output."""
    started_at = time.perf_counter()
    package_path = Path(package_dir or DEFAULT_PACKAGE_DIR)
    input_dir = package_path / "input"
    metadata_path = package_path / "handover" / "collection_metadata.json"
    log_dir = input_dir / "iis_logs"
    csv_path = input_dir / "iis_api_evidence.csv"

    metadata_result = validate_metadata(metadata_path)
    log_result = validate_iis_logs(log_dir)
    csv_result = csv_info(csv_path)
    analysis = analyze_records(csv_result["records"])
    errors = []
    errors.extend(metadata_result["errors"])
    errors.extend(log_result["errors"])
    errors.extend(csv_result["errors"])

    if analysis["legacy_requests"] != 0:
        errors.append("Legacy `/api/*` traffic was detected.")
    if analysis["django_requests"] <= 0:
        errors.append("Django `/api/v1/*` traffic was not confirmed.")
    if analysis["unknown_clients"] != 0:
        errors.append("Unknown API clients were detected.")

    accepted = not errors
    result = {
        "status": "EVIDENCE_ACCEPTED" if accepted else "EVIDENCE_REJECTED",
        "package_dir": str(package_path),
        "metadata": metadata_result["metadata"],
        "metadata_valid": not metadata_result["errors"],
        "iis_logs": log_result,
        "csv": {key: value for key, value in csv_result.items() if key != "records"},
        "traffic": {
            "total_requests": analysis["total_api_requests"],
            "legacy_requests": analysis["legacy_requests"],
            "django_requests": analysis["django_requests"],
            "unknown_clients": analysis["unknown_clients"],
            "error_requests": analysis["error_requests"],
            "error_rate": analysis["error_rate"],
            "known_clients": analysis["known_clients"],
        },
        "safety": {
            "shutdown_executed": False,
            "legacy_api_disabled": False,
            "iis_modified": False,
            "proxy_modified": False,
            "routes_changed": False,
            "database_modified": False,
        },
        "errors": errors,
        "decision": "EVIDENCE_ACCEPTED" if accepted else "EVIDENCE_REJECTED",
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    destination = Path(output_path or DEFAULT_STATUS_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    write_review(result, review_path=review_path)
    return result


def write_review(result, review_path=None):
    """Ghi review Markdown cho evidence handover."""
    destination = Path(review_path or DEFAULT_REVIEW_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    errors = result.get("errors") or []
    error_lines = "\n".join(f"- {error}" for error in errors) if errors else "- None"

    content = f"""# Phase 11.1.6.5.2 Evidence Handover Review

## Phase

Phase 11.1.6.5.2 - Production IIS Evidence Handover Package

## Scope

Handover package validation only. No shutdown, IIS route disablement, IIS
configuration change, proxy change, database change or production code change
was executed.

## Package

- Package directory: `{result["package_dir"]}`
- Metadata valid: `{result["metadata_valid"]}`
- IIS log count: `{result["iis_logs"]["count"]}`
- CSV path: `{result["csv"]["path"]}`
- CSV rows: `{result["csv"]["rows"]}`

## Traffic

| Metric | Count |
| --- | --- |
| Total requests | `{result["traffic"]["total_requests"]}` |
| Legacy `/api/*` requests | `{result["traffic"]["legacy_requests"]}` |
| Django `/api/v1/*` requests | `{result["traffic"]["django_requests"]}` |
| Unknown clients | `{result["traffic"]["unknown_clients"]}` |
| Error requests | `{result["traffic"]["error_requests"]}` |

## Errors

{error_lines}

## Decision

`{result["decision"]}`

## Next Action

Upload real IIS W3C logs, complete `collection_metadata.json`, export a
non-empty `iis_api_evidence.csv`, then rerun the acceptance validator.
"""
    destination.write_text(content, encoding="utf-8")
    return destination


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.6.5.2 evidence acceptance validator")
    parser.add_argument("--package-dir", default=None, help="Production evidence package directory.")
    parser.add_argument("--output", default=None, help="JSON status output path.")
    parser.add_argument("--review", default=None, help="Markdown review output path.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when evidence is rejected. Default rejected state exits 0.",
    )
    args = parser.parse_args()
    result = evaluate_acceptance(package_dir=args.package_dir, output_path=args.output, review_path=args.review)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "EVIDENCE_ACCEPTED":
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
