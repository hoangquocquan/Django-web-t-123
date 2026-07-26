"""Generate production-like API traffic for Phase 11.1.6.5.4.

Du lieu tao ra la simulation de test workflow migration. No khong phai traffic
production that va khong duoc dung nhu bang chung shutdown production.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "handover"
    / "production_like_traffic.json"
)
DEFAULT_REQUESTS = 1200
DEFAULT_DAYS = 7
REPLACEMENT_ENDPOINTS = [
    "/api/v1/login",
    "/api/v1/products",
    "/api/v1/orders",
    "/api/v1/customers",
    "/api/v1/catalog/products/",
    "/api/v1/sales/quotes/",
    "/api/v1/crm/contact-requests/",
]
USER_AGENTS = [
    "MecPrecisionPortal/1.0",
    "PartnerERP/3.2",
    "CRMWebhook/2.1",
    "SalesDashboard/4.0",
]
CLIENTS = ["10.0.0.10", "10.0.0.11", "10.0.0.12", "10.0.0.13", "10.0.0.14"]


def build_requests(total=DEFAULT_REQUESTS, days=DEFAULT_DAYS, seed=20260726):
    """Tao danh sach request chi di vao `/api/v1/*`, khong tao legacy `/api/*`."""
    rng = random.Random(seed)
    count = max(1, int(total))
    window_days = max(1, int(days))
    start = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=window_days)
    requests = []

    for index in range(count):
        offset_seconds = int((window_days * 24 * 60 * 60) * (index / count))
        timestamp = start + timedelta(seconds=offset_seconds)
        endpoint = rng.choice(REPLACEMENT_ENDPOINTS)
        status_code = rng.choices([200, 201, 204, 400, 404, 500], weights=[82, 8, 4, 3, 2, 1], k=1)[0]
        requests.append(
            {
                "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
                "client": rng.choice(CLIENTS),
                "method": rng.choice(["GET", "POST", "PUT"]),
                "endpoint": endpoint,
                "status_code": status_code,
                "user_agent": rng.choice(USER_AGENTS),
            }
        )

    return requests


def summarize(requests):
    """Tinh so request legacy va Django replacement trong traffic simulation."""
    legacy_count = sum(1 for item in requests if item["endpoint"].startswith("/api/") and not item["endpoint"].startswith("/api/v1/"))
    django_count = sum(1 for item in requests if item["endpoint"] == "/api/v1" or item["endpoint"].startswith("/api/v1/"))
    unknown_clients = sum(1 for item in requests if not item.get("client"))
    return {
        "total_requests": len(requests),
        "legacy_requests": legacy_count,
        "django_requests": django_count,
        "unknown_clients": unknown_clients,
    }


def generate_traffic(output_path=None, requests=DEFAULT_REQUESTS, days=DEFAULT_DAYS, seed=20260726):
    """Ghi file JSON traffic simulation."""
    traffic = build_requests(total=requests, days=days, seed=seed)
    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "simulation": True,
        "environment": "STAGING_SIMULATION",
        "days": int(days),
        "summary": summarize(traffic),
        "requests": traffic,
    }
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload | {"output": str(output)}


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Generate production-like API traffic")
    parser.add_argument("--output", default=None, help="Traffic JSON output path.")
    parser.add_argument("--requests", type=int, default=DEFAULT_REQUESTS, help="Number of requests to generate.")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help="Traffic window in days.")
    parser.add_argument("--seed", type=int, default=20260726, help="Deterministic random seed.")
    args = parser.parse_args()
    result = generate_traffic(output_path=args.output, requests=args.requests, days=args.days, seed=args.seed)
    printable = {key: value for key, value in result.items() if key != "requests"}
    print(json.dumps(printable, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
