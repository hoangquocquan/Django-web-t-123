"""Phase 12.2 local load-test scenario helper.

This helper is intentionally lightweight. It uses Django's local test client and
worker threads to simulate concurrency without contacting production.
"""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DJANGO_ROOT = PROJECT_ROOT / "django_backend"
if str(DJANGO_ROOT) not in sys.path:
    sys.path.insert(0, str(DJANGO_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")


LOAD_LEVELS = {
    "light": 10,
    "medium": 50,
    "stress": 100,
}

DEFAULT_ENDPOINTS = [
    "/api/v1/health/",
    "/api/v1/catalog/products/?limit=5",
    "/api/v1/public/home/",
]


def build_client():
    """Create a Django test client."""
    import django
    from django.conf import settings
    from django.test import Client

    django.setup()
    if "testserver" not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append("testserver")
    return Client()


def request_endpoint(path):
    """Request one endpoint and return timing data."""
    client = build_client()
    start = time.perf_counter()
    response = client.get(path)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return {"path": path, "status_code": response.status_code, "latency_ms": elapsed_ms}


def percentile(values, percentile_value):
    """Return percentile from sorted values."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * (percentile_value / 100)))
    return ordered[max(0, min(index, len(ordered) - 1))]


def run_load_scenario(level="light", endpoints=None):
    """Run a local threaded load scenario."""
    users = LOAD_LEVELS[level]
    endpoint_list = endpoints or DEFAULT_ENDPOINTS
    planned_requests = [endpoint_list[index % len(endpoint_list)] for index in range(users)]
    start = time.perf_counter()
    results = []

    with ThreadPoolExecutor(max_workers=min(users, 20)) as executor:
        futures = [executor.submit(request_endpoint, path) for path in planned_requests]
        for future in as_completed(futures):
            results.append(future.result())

    elapsed_seconds = time.perf_counter() - start
    latencies = [item["latency_ms"] for item in results]
    failures = [item for item in results if item["status_code"] >= 400]
    return {
        "level": level,
        "users": users,
        "request_count": len(results),
        "requests_per_second": round(len(results) / elapsed_seconds, 4) if elapsed_seconds else 0,
        "average_latency_ms": round(sum(latencies) / len(latencies), 4) if latencies else 0,
        "p95_latency_ms": round(percentile(latencies, 95), 4),
        "failure_count": len(failures),
        "failure_rate": round(len(failures) / len(results), 4) if results else 0,
        "production_modified": False,
    }


def main():
    """Run all load levels and print JSON."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    payload = {level: run_load_scenario(level) for level in LOAD_LEVELS}
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
