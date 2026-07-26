"""Generate IIS W3C style evidence from production-like traffic.

Script nay tao IIS log va CSV evidence tu traffic simulation. No khong doc hay
sua production, khong shutdown, khong disable routes va khong bypass validator.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.phase11_1_6_5_4_generate_production_like_traffic import DEFAULT_OUTPUT as DEFAULT_TRAFFIC_PATH
    from scripts.phase11_1_6_5_4_generate_production_like_traffic import generate_traffic
except ModuleNotFoundError:
    from phase11_1_6_5_4_generate_production_like_traffic import DEFAULT_OUTPUT as DEFAULT_TRAFFIC_PATH
    from phase11_1_6_5_4_generate_production_like_traffic import generate_traffic


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_DIR = PROJECT_ROOT / "docs" / "migration" / "production_evidence"
DEFAULT_LOG_PATH = DEFAULT_EVIDENCE_DIR / "input" / "iis_logs" / "u_ex_simulated.log"
DEFAULT_CSV_PATH = DEFAULT_EVIDENCE_DIR / "input" / "iis_api_evidence.csv"
DEFAULT_METADATA_PATH = DEFAULT_EVIDENCE_DIR / "handover" / "collection_metadata.json"
REQUIRED_CSV_FIELDS = ["timestamp", "source", "client", "endpoint", "status_code", "user_agent"]


def load_or_create_traffic(path=None, requests=1200, days=7):
    """Doc traffic JSON, neu chua co thi tu tao moi."""
    traffic_path = Path(path or DEFAULT_TRAFFIC_PATH)
    if not traffic_path.exists():
        return generate_traffic(output_path=traffic_path, requests=requests, days=days), traffic_path
    return json.loads(traffic_path.read_text(encoding="utf-8")), traffic_path


def parse_timestamp(value):
    """Chuyen timestamp ISO sang datetime UTC."""
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def write_iis_log(requests, log_path=None):
    """Ghi IIS W3C compatible log tu danh sach request."""
    path = Path(log_path or DEFAULT_LOG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "#Software: Microsoft Internet Information Services 10.0",
        "#Version: 1.0",
        "#Fields: date time c-ip cs-method cs-uri-stem sc-status cs(User-Agent)",
    ]
    for item in requests:
        timestamp = parse_timestamp(item["timestamp"])
        lines.append(
            " ".join(
                [
                    timestamp.strftime("%Y-%m-%d"),
                    timestamp.strftime("%H:%M:%S"),
                    item.get("client") or "-",
                    item.get("method") or "GET",
                    item.get("endpoint") or "-",
                    str(item.get("status_code") or 200),
                    str(item.get("user_agent") or "ProductionLikeClient").replace(" ", "+"),
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_csv(requests, csv_path=None, source_path=None):
    """Ghi CSV evidence voi format collector dang yeu cau."""
    path = Path(csv_path or DEFAULT_CSV_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=REQUIRED_CSV_FIELDS)
        writer.writeheader()
        for item in requests:
            writer.writerow(
                {
                    "timestamp": item["timestamp"],
                    "source": str(source_path or DEFAULT_LOG_PATH),
                    "client": item.get("client") or "",
                    "endpoint": item.get("endpoint") or "",
                    "status_code": item.get("status_code") or 200,
                    "user_agent": item.get("user_agent") or "ProductionLikeClient",
                }
            )
    return path


def write_metadata(requests, metadata_path=None):
    """Ghi metadata STAGING_SIMULATION cho handover package."""
    path = Path(metadata_path or DEFAULT_METADATA_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamps = sorted(parse_timestamp(item["timestamp"]) for item in requests)
    metadata = {
        "server": "TRAINING-IIS-SERVER",
        "environment": "STAGING_SIMULATION",
        "iis_site": "MECPrecision-Web",
        "site_id": "1",
        "collection_start": timestamps[0].strftime("%Y-%m-%d") if timestamps else "NOT_PROVIDED",
        "collection_end": timestamps[-1].strftime("%Y-%m-%d") if timestamps else "NOT_PROVIDED",
        "operator": "training-user",
        "reviewer": "architect-review",
        "notes": "Production-like simulation evidence. Not real production IIS traffic.",
    }
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return metadata


def generate_iis_evidence(traffic_path=None, log_path=None, csv_path=None, metadata_path=None, requests=1200, days=7):
    """Tao IIS log, CSV va metadata tu traffic simulation."""
    traffic_payload, source_traffic_path = load_or_create_traffic(path=traffic_path, requests=requests, days=days)
    request_items = traffic_payload.get("requests", [])
    output_log = write_iis_log(request_items, log_path=log_path)
    output_csv = write_csv(request_items, csv_path=csv_path, source_path=output_log)
    metadata = write_metadata(request_items, metadata_path=metadata_path)
    summary = traffic_payload.get("summary", {})
    return {
        "simulation": True,
        "environment": "STAGING_SIMULATION",
        "traffic_path": str(source_traffic_path),
        "iis_log_path": str(output_log),
        "csv_path": str(output_csv),
        "metadata_path": str(Path(metadata_path or DEFAULT_METADATA_PATH)),
        "metadata": metadata,
        "total_requests": summary.get("total_requests", len(request_items)),
        "legacy_requests": summary.get("legacy_requests", 0),
        "django_requests": summary.get("django_requests", len(request_items)),
        "unknown_clients": summary.get("unknown_clients", 0),
    }


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Generate IIS W3C evidence from production-like traffic")
    parser.add_argument("--traffic", default=None, help="Traffic JSON input path.")
    parser.add_argument("--log", default=None, help="IIS W3C log output path.")
    parser.add_argument("--csv", default=None, help="CSV evidence output path.")
    parser.add_argument("--metadata", default=None, help="Metadata JSON output path.")
    parser.add_argument("--requests", type=int, default=1200, help="Request count when traffic must be generated.")
    parser.add_argument("--days", type=int, default=7, help="Traffic window when traffic must be generated.")
    args = parser.parse_args()
    result = generate_iis_evidence(
        traffic_path=args.traffic,
        log_path=args.log,
        csv_path=args.csv,
        metadata_path=args.metadata,
        requests=args.requests,
        days=args.days,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
