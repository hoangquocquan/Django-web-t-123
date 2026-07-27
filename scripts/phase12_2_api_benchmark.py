"""Phase 12.2 local API benchmark.

The benchmark uses Django's test client against the local migration test
settings. It does not call production and does not modify production systems.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DJANGO_ROOT = PROJECT_ROOT / "django_backend"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "performance" / "api_benchmark_result.json"

if str(DJANGO_ROOT) not in sys.path:
    sys.path.insert(0, str(DJANGO_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")


GET_SCENARIOS = [
    ("health_legacy_compat", "GET", "/api/health/", None, {}),
    ("health_v1", "GET", "/api/v1/health/", None, {}),
    ("public_home", "GET", "/api/v1/public/home/", None, {}),
    ("catalog_products", "GET", "/api/v1/catalog/products/?limit=5&offset=0", None, {}),
    ("catalog_categories", "GET", "/api/v1/catalog/categories/?limit=5&offset=0", None, {}),
    ("crm_customers", "GET", "/api/v1/crm/customers/?limit=5&offset=0", None, {}),
    ("sales_quotes", "GET", "/api/v1/sales/quotes/?limit=5&offset=0", None, {}),
    ("cms_pages", "GET", "/api/v1/cms/pages/?limit=5&offset=0", None, {}),
    ("auth_profile", "GET", "/api/v1/auth/profile/?admin_id=1", None, {}),
    ("auth_permissions", "GET", "/api/v1/auth/permissions/?role=viewer", None, {}),
    ("news", "GET", "/api/v1/news/?limit=5&offset=0", None, {}),
]

POST_SCENARIOS = [
    (
        "contact_create_intent",
        "POST",
        "/api/v1/crm/contact-requests/",
        {"name": "Performance Contact", "email": "perf@example.com", "message": "Performance baseline", "captcha_answer": "7"},
        {},
    ),
    (
        "quote_create_intent",
        "POST",
        "/api/v1/sales/quotes/",
        {"name": "Performance Quote", "email": "quote@example.com", "product": "CNC shaft", "quantity": "10"},
        {},
    ),
    (
        "ai_chat",
        "POST",
        "/api/v1/ai/chat/",
        {"question": "MecPrecision có gia công CNC không?"},
        {},
    ),
    (
        "product_create_intent",
        "POST",
        "/api/v1/catalog/products/",
        {
            "category_id": "1",
            "name": "Performance Product",
            "short_description": "Performance baseline",
            "description": "Performance baseline product intent",
            "main_image": "/images/performance.jpg",
            "status": "draft",
        },
        {"HTTP_X_ADMIN_TOKEN": "dev-admin-token"},
    ),
]


def utc_now():
    """Return an ISO timestamp for audit records."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def percentile(values, percentile_value):
    """Return percentile from a small sorted sample."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * (percentile_value / 100)))
    return ordered[max(0, min(index, len(ordered) - 1))]


def build_client():
    """Create a Django test client after setup."""
    import django
    from django.conf import settings
    from django.test import Client

    django.setup()
    if "testserver" not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append("testserver")
    return Client()


def execute_request(client, method, path, payload=None, headers=None):
    """Run one request and return status plus latency in milliseconds."""
    headers = headers or {}
    start = time.perf_counter()
    if method == "GET":
        response = client.get(path, **headers)
    else:
        response = client.post(path, data=json.dumps(payload or {}), content_type="application/json", **headers)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return response.status_code, elapsed_ms


def run_scenario(client, scenario, iterations):
    """Benchmark one endpoint scenario."""
    name, method, path, payload, headers = scenario
    latencies = []
    errors = []
    for _ in range(iterations):
        status_code, latency_ms = execute_request(client, method, path, payload=payload, headers=headers)
        latencies.append(latency_ms)
        if status_code >= 400:
            errors.append({"status_code": status_code, "path": path})

    total_ms = sum(latencies)
    return {
        "name": name,
        "method": method,
        "path": path,
        "request_count": iterations,
        "average_latency_ms": round(statistics.mean(latencies), 4),
        "p95_latency_ms": round(percentile(latencies, 95), 4),
        "p99_latency_ms": round(percentile(latencies, 99), 4),
        "min_latency_ms": round(min(latencies), 4),
        "max_latency_ms": round(max(latencies), 4),
        "throughput_requests_per_second": round((iterations / total_ms) * 1000, 4) if total_ms else 0,
        "error_count": len(errors),
        "error_rate": round(len(errors) / iterations, 4) if iterations else 0,
        "errors": errors[:5],
    }


def run_benchmark(iterations=5, output_path=None, scenarios=None):
    """Run all benchmark scenarios and write the JSON result."""
    client = build_client()
    selected_scenarios = scenarios or (GET_SCENARIOS + POST_SCENARIOS)
    tracemalloc.start()
    cpu_start = time.process_time()
    wall_start = time.perf_counter()
    scenario_results = [run_scenario(client, scenario, iterations) for scenario in selected_scenarios]
    current_memory, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    wall_elapsed = time.perf_counter() - wall_start
    cpu_elapsed = time.process_time() - cpu_start

    total_requests = sum(item["request_count"] for item in scenario_results)
    total_errors = sum(item["error_count"] for item in scenario_results)
    all_latencies = []
    for item in scenario_results:
        all_latencies.extend([item["average_latency_ms"]] * item["request_count"])

    result = {
        "phase": "12.2",
        "created_at": utc_now(),
        "environment": "LOCAL_DJANGO_TEST_CLIENT",
        "production_modified": False,
        "routes_changed": False,
        "database_schema_changed": False,
        "iterations_per_scenario": iterations,
        "scenario_count": len(scenario_results),
        "request_count": total_requests,
        "average_latency_ms": round(statistics.mean(all_latencies), 4) if all_latencies else 0,
        "p95_latency_ms": round(percentile(all_latencies, 95), 4),
        "p99_latency_ms": round(percentile(all_latencies, 99), 4),
        "throughput_requests_per_second": round(total_requests / wall_elapsed, 4) if wall_elapsed else 0,
        "error_count": total_errors,
        "error_rate": round(total_errors / total_requests, 4) if total_requests else 0,
        "cpu_time_seconds": round(cpu_elapsed, 4),
        "wall_time_seconds": round(wall_elapsed, 4),
        "memory_current_bytes": current_memory,
        "memory_peak_bytes": peak_memory,
        "scenarios": scenario_results,
        "status": "API_BENCHMARK_COMPLETE" if total_errors == 0 else "API_BENCHMARK_COMPLETE_WITH_ERRORS",
    }

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 12.2 local API benchmark")
    parser.add_argument("--iterations", type=int, default=5, help="Requests per scenario.")
    parser.add_argument("--output", default=None, help="Output JSON path.")
    args = parser.parse_args()

    result = run_benchmark(iterations=args.iterations, output_path=args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
