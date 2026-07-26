"""Phase 11.1.6.5.1 IIS collection evidence validator.

Script này kiểm tra gói evidence được tạo từ IIS production logs. Nó chỉ đọc
file evidence và ghi báo cáo; không shutdown, không sửa IIS, không sửa route,
không sửa proxy và không sửa database.
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
    from scripts.phase11_1_6_2_real_production_evidence import (
        analyze_records,
        infer_collection_period,
        read_records,
    )
except ModuleNotFoundError:
    from phase11_1_6_2_real_production_evidence import analyze_records, infer_collection_period, read_records


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = PROJECT_ROOT / "docs" / "migration" / "production_evidence" / "input"
DEFAULT_CSV_PATH = DEFAULT_INPUT_DIR / "iis_api_evidence.csv"
DEFAULT_LOG_DIR = DEFAULT_INPUT_DIR / "iis_logs"
DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "reports"
    / "REAL_PRODUCTION_EVIDENCE_REPORT.json"
)
DEFAULT_REVIEW_PATH = PROJECT_ROOT / "docs" / "reviews" / "PHASE_11.1.6.5.1_COLLECTION_RESULT.md"
REQUIRED_CSV_FIELDS = ["timestamp", "source", "client", "endpoint", "status_code", "user_agent"]


def discover_iis_logs(input_dir=None):
    """Tim cac raw IIS W3C log u_ex*.log trong thu muc input."""
    directory = Path(input_dir or DEFAULT_INPUT_DIR)
    log_dir = directory / "iis_logs"
    files = []
    if log_dir.exists():
        files.extend(log_dir.rglob("u_ex*.log"))
        files.extend(log_dir.rglob("*.log"))
    files.extend(directory.glob("u_ex*.log"))
    return sorted({path for path in files if path.is_file()})


def csv_metadata(csv_path=None):
    """Kiem tra CSV export co dung cot va co du lieu hay khong."""
    path = Path(csv_path or DEFAULT_CSV_PATH)
    errors = []
    fields = []
    rows = 0

    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "fields": fields,
            "rows": rows,
            "errors": [f"CSV evidence export does not exist: {path}."],
        }

    with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as file:
        reader = csv.DictReader(file)
        fields = list(reader.fieldnames or [])
        rows = sum(1 for _ in reader)

    missing_fields = [field for field in REQUIRED_CSV_FIELDS if field not in fields]
    if missing_fields:
        errors.append(f"CSV evidence export is missing required fields: {', '.join(missing_fields)}.")
    if rows <= 0:
        errors.append("CSV evidence export is empty.")

    return {
        "path": str(path),
        "exists": True,
        "fields": fields,
        "rows": rows,
        "errors": errors,
    }


def read_csv_evidence(csv_path=None):
    """Doc CSV export lam nguon dem traffic chinh de tranh dem trung raw logs."""
    path = Path(csv_path or DEFAULT_CSV_PATH)
    if not path.exists():
        return []
    return read_records(path)


def build_report(input_dir=None, output_path=None, review_path=None, period=None):
    """Kiem tra gói collection va ghi JSON/Markdown report."""
    started_at = time.perf_counter()
    input_path = Path(input_dir or DEFAULT_INPUT_DIR)
    csv_path = input_path / "iis_api_evidence.csv"
    logs = discover_iis_logs(input_path)
    csv_info = csv_metadata(csv_path)
    records = read_csv_evidence(csv_path)
    analysis = analyze_records(records)
    collection_period = infer_collection_period(records, explicit_period=period)
    errors = []

    if not input_path.exists():
        errors.append(f"Evidence input folder does not exist: {input_path}.")
    if not logs:
        errors.append("IIS logs were not found.")
    errors.extend(csv_info["errors"])
    if collection_period == "NOT_PROVIDED":
        errors.append("Collection period is not provided.")
    if analysis["legacy_requests"] != 0:
        errors.append("Legacy `/api/*` traffic was detected.")
    if analysis["django_requests"] <= 0:
        errors.append("Django `/api/v1/*` traffic was not confirmed.")
    if analysis["unknown_clients"] != 0:
        errors.append("Unknown API clients were detected.")

    complete = not errors
    report = {
        "status": "COMPLETE_EVIDENCE_PACKAGE" if complete else "INCOMPLETE_EVIDENCE_PACKAGE",
        "ready_for_shutdown": complete,
        "server": "Windows Server IIS",
        "environment": "production",
        "input_folder": str(input_path),
        "collection_period": collection_period,
        "log_files_collected": len(logs),
        "log_files": [str(path) for path in logs],
        "csv_evidence": csv_info,
        "total_requests": analysis["total_api_requests"],
        "legacy_requests": analysis["legacy_requests"],
        "django_requests": analysis["django_requests"],
        "unknown_clients": analysis["unknown_clients"],
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
        "decision": "COMPLETE_EVIDENCE_PACKAGE" if complete else "INCOMPLETE_EVIDENCE_PACKAGE",
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    destination = Path(output_path or DEFAULT_OUTPUT_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_review(report, review_path=review_path)
    return report


def write_review(report, review_path=None):
    """Ghi file Markdown tom tat ket qua collection cho reviewer."""
    destination = Path(review_path or DEFAULT_REVIEW_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    error_lines = "\n".join(f"- {error}" for error in report["errors"]) if report["errors"] else "- None"
    log_lines = "\n".join(f"- `{path}`" for path in report["log_files"]) if report["log_files"] else "- None"

    content = f"""# Phase 11.1.6.5.1 Collection Result

## Phase

Phase 11.1.6.5.1 - Production IIS Log Collection Execution

## Scope

Evidence collection validation only. No shutdown, route change, IIS change,
proxy change, production code change or database change was executed.

## Environment

- Server: `{report["server"]}`
- Environment: `{report["environment"]}`
- Collection period: `{report["collection_period"]}`

## Log Files Collected

Count: `{report["log_files_collected"]}`

{log_lines}

## CSV Evidence

- Path: `{report["csv_evidence"]["path"]}`
- Exists: `{report["csv_evidence"]["exists"]}`
- Rows: `{report["csv_evidence"]["rows"]}`

## Traffic Analysis

| Metric | Count |
| --- | --- |
| Total requests | `{report["total_requests"]}` |
| Legacy `/api/*` requests | `{report["legacy_requests"]}` |
| Django `/api/v1/*` requests | `{report["django_requests"]}` |
| Unknown clients | `{report["unknown_clients"]}` |

## Errors

{error_lines}

## Safety

- Shutdown executed: `{report["shutdown_executed"]}`
- Legacy routes disabled: `{report["legacy_routes_disabled"]}`
- IIS modified: `{report["iis_modified"]}`
- Proxy modified: `{report["proxy_modified"]}`
- Routes changed: `{report["routes_changed"]}`
- Database modified: `{report["database_modified"]}`

## Decision

`{report["decision"]}`
"""
    destination.write_text(content, encoding="utf-8")
    return destination


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.6.5.1 IIS collection validator")
    parser.add_argument("--input-dir", default=None, help="Evidence input folder.")
    parser.add_argument("--output", default=None, help="JSON report output path.")
    parser.add_argument("--review", default=None, help="Markdown review output path.")
    parser.add_argument("--period", default=None, help="Collection period label.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when package is incomplete. Default incomplete state exits 0.",
    )
    args = parser.parse_args()
    result = build_report(
        input_dir=args.input_dir,
        output_path=args.output,
        review_path=args.review,
        period=args.period,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "COMPLETE_EVIDENCE_PACKAGE":
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
