"""Run a bounded HTTP load smoke test against the local staging runtime."""

from __future__ import annotations

import argparse
import json
import math
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "evidence" / "prod-06" / "load-test-results.json"
ENDPOINTS = (
    ("health", "/api/v1/health/", {200}),
    ("dashboard", "/api/v1/admin/dashboard/", {200, 401, 403}),
    ("customer", "/api/v1/crm/customers/?limit=5", {200, 401, 403}),
    ("lead", "/api/v1/sales/leads/?limit=5", {200, 401, 403}),
    ("quotation", "/api/v1/sales/quotations/?limit=5", {200, 401, 403}),
    ("knowledge", "/api/v1/knowledge/health/", {200, 401, 403}),
    ("ai", "/api/v1/ai/health/", {200, 401, 403}),
)


def percentile(values, value):
    """Calculate a nearest-rank percentile without third-party packages."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(value / 100 * len(ordered)) - 1))
    return round(ordered[index], 2)


def one_request(base_url, endpoint):
    """Perform one safe GET request and retain timing/status only."""
    name, path, expected = endpoint
    request = urllib.request.Request(
        f"{base_url}{path}", headers={"X-Forwarded-Proto": "https", "Host": "localhost"}
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # nosec B310 - base URL is loopback-only
            status = response.status
            response.read(512)
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.read(512)
    except (OSError, urllib.error.URLError) as exc:
        return {
            "name": name,
            "latency_ms": 0,
            "status_code": None,
            "ok": False,
            "error": str(exc),
        }
    latency = (time.perf_counter() - started) * 1000
    return {
        "name": name,
        "latency_ms": latency,
        "status_code": status,
        "ok": status in expected,
    }


def run_load(base_url, virtual_users=20, requests=140):
    """Run a read-only mixed-endpoint load smoke and summarize percentiles."""
    parsed = urlparse(base_url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError("Load smoke is restricted to local HTTP staging endpoints")
    started = time.perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=virtual_users) as executor:
        futures = [
            executor.submit(one_request, base_url, ENDPOINTS[index % len(ENDPOINTS)])
            for index in range(requests)
        ]
        for future in as_completed(futures):
            results.append(future.result())
    elapsed = time.perf_counter() - started
    latencies = [item["latency_ms"] for item in results if item["latency_ms"] > 0]
    errors = [item for item in results if not item["ok"]]
    endpoints = {}
    for name, _, _ in ENDPOINTS:
        scoped = [item for item in results if item["name"] == name]
        endpoints[name] = {
            "requests": len(scoped),
            "errors": sum(not item["ok"] for item in scoped),
            "p95_ms": percentile([item["latency_ms"] for item in scoped], 95),
        }
    error_rate = len(errors) / len(results) if results else 1.0
    p95 = percentile(latencies, 95)
    return {
        "phase": "PROD-06",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "PASS" if error_rate <= 0.01 and p95 <= 2000 else "FAIL",
        "virtual_users": virtual_users,
        "requests": len(results),
        "duration_seconds": round(elapsed, 2),
        "requests_per_second": round(len(results) / elapsed, 2) if elapsed else 0,
        "errors": len(errors),
        "error_rate": round(error_rate, 4),
        "p50_ms": percentile(latencies, 50),
        "p95_ms": p95,
        "p99_ms": percentile(latencies, 99),
        "thresholds": {"max_error_rate": 0.01, "max_p95_ms": 2000},
        "endpoints": endpoints,
        "bottleneck": max(endpoints, key=lambda key: endpoints[key]["p95_ms"]),
        "safety": {"read_only_requests": True, "production_modified": False},
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--virtual-users", type=int, default=20)
    parser.add_argument("--requests", type=int, default=140)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    if not 1 <= args.virtual_users <= 100 or not 1 <= args.requests <= 5000:
        parser.error("virtual-users must be 1..100 and requests must be 1..5000")
    report = run_load(args.base_url.rstrip("/"), args.virtual_users, args.requests)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
