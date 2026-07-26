"""Phase 11.1.6.5 real production evidence validator.

Script này chỉ đọc evidence production và tạo báo cáo. Nó không tắt Legacy API,
không sửa IIS, không sửa proxy, không đổi route và không sửa database.
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
DEFAULT_REPORT_PATH = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "reports"
    / "REAL_PRODUCTION_EVIDENCE_REPORT.json"
)
DEFAULT_REVIEW_PATH = PROJECT_ROOT / "docs" / "reviews" / "PHASE_11.1.6.5_PRODUCTION_EVIDENCE_REVIEW.md"
DEFAULT_CSV_PATH = DEFAULT_INPUT_DIR / "iis_api_evidence.csv"
DEFAULT_IIS_LOG_DIR = DEFAULT_INPUT_DIR / "iis_logs"

SUPPORTED_SUFFIXES = {".csv", ".json", ".jsonl", ".ndjson", ".log", ".txt"}
REQUIRED_CSV_FIELDS = ["timestamp", "source", "client", "endpoint", "status_code", "user_agent"]


def read_collection_metadata(input_dir=None):
    """Doc metadata handover neu co de report khong nham simulation voi production that."""
    directory = Path(input_dir or DEFAULT_INPUT_DIR)
    metadata_path = directory.parent / "handover" / "collection_metadata.json"
    if not metadata_path.exists():
        return {}
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return metadata if isinstance(metadata, dict) else {}


def is_template_file(path):
    """Bo qua file mau de khong tinh nham thanh evidence production that."""
    return Path(path).name.upper().endswith("_TEMPLATE.CSV")


def discover_evidence_files(input_dir=None):
    """Tim cac file evidence co the phan tich trong thu muc input."""
    directory = Path(input_dir or DEFAULT_INPUT_DIR)
    if not directory.exists():
        return []
    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES and not is_template_file(path)
    )


def discover_iis_logs(input_dir=None):
    """Tim raw IIS W3C log trong input/iis_logs hoac cac file .log ben duoi input."""
    directory = Path(input_dir or DEFAULT_INPUT_DIR)
    log_dir = directory / "iis_logs"
    candidates = []
    if log_dir.exists():
        candidates.extend(path for path in log_dir.rglob("*.log") if path.is_file())
    candidates.extend(path for path in directory.glob("*.log") if path.is_file())
    return sorted(set(candidates))


def read_csv_fieldnames(path):
    """Doc header CSV de kiem tra cac cot bat buoc."""
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or [])


def count_csv_rows(path):
    """Dem so dong du lieu trong CSV, khong tinh dong header."""
    csv_path = Path(path)
    if not csv_path.exists():
        return 0
    with csv_path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as file:
        reader = csv.DictReader(file)
        return sum(1 for _ in reader)


def validate_csv_export(csv_path=None):
    """Kiem tra CSV export co ton tai, co dung cot va co du lieu."""
    path = Path(csv_path or DEFAULT_CSV_PATH)
    errors = []
    fieldnames = read_csv_fieldnames(path)
    row_count = count_csv_rows(path)

    if not path.exists():
        errors.append(f"CSV export does not exist: {path}.")
    missing_fields = [field for field in REQUIRED_CSV_FIELDS if field not in fieldnames]
    if missing_fields:
        errors.append(f"CSV export is missing required fields: {', '.join(missing_fields)}.")
    if row_count <= 0:
        errors.append("CSV export is empty.")

    return {
        "path": str(path),
        "exists": path.exists(),
        "fieldnames": fieldnames,
        "row_count": row_count,
        "errors": errors,
    }


def build_data_sources(files):
    """Tao danh sach nguon du lieu va so record doc duoc tu tung file."""
    sources = []
    records = []
    errors = []

    for path in files:
        try:
            file_records = read_records(path)
        except OSError as exc:
            errors.append(f"Cannot read evidence file {path}: {exc}.")
            file_records = []
        records.extend(file_records)
        sources.append({"path": str(path), "records": len(file_records), "type": path.suffix.lower().lstrip(".")})

    return records, sources, errors


def validate_production_evidence_package(input_dir=None, output_path=None, review_path=None, period=None):
    """Doc evidence production va quyet dinh COMPLETE hay INCOMPLETE."""
    started_at = time.perf_counter()
    input_path = Path(input_dir or DEFAULT_INPUT_DIR)
    files = discover_evidence_files(input_path)
    iis_logs = discover_iis_logs(input_path)
    csv_check = validate_csv_export(input_path / "iis_api_evidence.csv")
    records, data_sources, errors = build_data_sources(files)
    analysis = analyze_records(records)
    collection_period = infer_collection_period(records, explicit_period=period)
    metadata = read_collection_metadata(input_path)

    if not input_path.exists():
        errors.append(f"Evidence input directory does not exist: {input_path}.")
    if not files:
        errors.append("No production evidence files were found.")
    if not iis_logs:
        errors.append("IIS W3C logs were not found in the evidence input.")
    if not records:
        errors.append("No evidence records were found.")
    if collection_period == "NOT_PROVIDED":
        errors.append("Collection period is not provided.")
    errors.extend(csv_check["errors"])
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
        "environment": metadata.get("environment") or "production",
        "server": metadata.get("server") or "Windows Server IIS",
        "iis_site": metadata.get("iis_site"),
        "site_id": metadata.get("site_id"),
        "simulation": str(metadata.get("environment", "")).upper() == "STAGING_SIMULATION",
        "input_dir": str(input_path),
        "collection_period": collection_period,
        "data_sources": data_sources,
        "required_files": {
            "iis_logs_found": len(iis_logs),
            "csv_export": csv_check,
        },
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

    destination = Path(output_path or DEFAULT_REPORT_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_review_report(report, review_path=review_path)
    return report


def write_review_report(report, review_path=None):
    """Ghi bao cao Markdown cho architecture reviewer de doc nhanh."""
    destination = Path(review_path or DEFAULT_REVIEW_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    errors = report.get("errors") or []
    error_lines = "\n".join(f"- {error}" for error in errors) if errors else "- None"
    source_lines = "\n".join(
        f"- `{source['path']}`: {source['records']} records ({source['type']})"
        for source in report.get("data_sources", [])
    )
    if not source_lines:
        source_lines = "- None"

    content = f"""# Phase 11.1.6.5 Production Evidence Review

## Phase

Phase 11.1.6.5 - Real Production Evidence Acquisition

## Scope

Evidence-only validation. No shutdown, IIS modification, proxy change, route
change, production code change or database change was executed.

## Environment

- Environment: `{report.get("environment")}`
- Server: `{report.get("server")}`
- Collection period: `{report.get("collection_period")}`

## Data Sources

{source_lines}

## Traffic Counts

| Metric | Value |
| --- | --- |
| Total API requests | `{report.get("total_requests")}` |
| Legacy `/api/*` requests | `{report.get("legacy_requests")}` |
| Django `/api/v1/*` requests | `{report.get("django_requests")}` |
| Unknown clients | `{report.get("unknown_clients")}` |
| Error requests | `{report.get("error_requests")}` |
| Error rate | `{report.get("error_rate")}` |

## Required File Check

- IIS logs found: `{report.get("required_files", {}).get("iis_logs_found")}`
- CSV export path: `{report.get("required_files", {}).get("csv_export", {}).get("path")}`
- CSV rows: `{report.get("required_files", {}).get("csv_export", {}).get("row_count")}`

## Errors

{error_lines}

## Safety Confirmation

- Legacy routes disabled: `{report.get("legacy_routes_disabled")}`
- Routes changed: `{report.get("routes_changed")}`
- Proxy modified: `{report.get("proxy_modified")}`
- IIS modified: `{report.get("iis_modified")}`
- Database modified: `{report.get("database_modified")}`
- Shutdown executed: `{report.get("shutdown_executed")}`

## Decision

`{report.get("decision")}`

## Next Action

Provide real IIS production logs and a non-empty CSV export covering at least 7
days before rerunning the final readiness gate.
"""
    destination.write_text(content, encoding="utf-8")
    return destination


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.6.5 production evidence acquisition validator")
    parser.add_argument("--input-dir", default=None, help="Evidence input directory.")
    parser.add_argument("--output", default=None, help="JSON report output path.")
    parser.add_argument("--review", default=None, help="Markdown review output path.")
    parser.add_argument("--period", default=None, help="Collection period label.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when evidence is incomplete. Default incomplete state exits 0.",
    )
    args = parser.parse_args()
    result = validate_production_evidence_package(
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
