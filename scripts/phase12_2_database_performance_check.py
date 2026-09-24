"""Phase 12.2 legacy SQLite performance check.

The script opens the legacy SQLite database in read-only mode and measures a
small set of representative queries. It does not change schema or data.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = PROJECT_ROOT / "backend" / "database" / "mecprecision.sqlite"
DEFAULT_REPORT = PROJECT_ROOT / "docs" / "performance" / "database_performance_report.md"
DEFAULT_JSON = PROJECT_ROOT / "docs" / "performance" / "database_performance_result.json"
DEFAULT_DASHBOARD = PROJECT_ROOT / "docs" / "reviews" / "PHASE_12.2_PERFORMANCE_REPORT.md"
DEFAULT_API_RESULT = PROJECT_ROOT / "docs" / "performance" / "api_benchmark_result.json"

QUERIES = [
    ("product_count", "SELECT COUNT(*) FROM products"),
    (
        "product_list_join_category",
        """
        SELECT p.id, p.name, c.name
        FROM products p
        LEFT JOIN product_categories c ON c.id = p.category_id
        ORDER BY p.id
        LIMIT 20
        """,
    ),
    (
        "quote_customer_join",
        """
        SELECT q.id, q.project_name, c.company_name
        FROM quote_requests q
        LEFT JOIN customers c ON c.id = q.customer_id
        ORDER BY q.id
        LIMIT 20
        """,
    ),
    (
        "cms_pages_by_slug",
        "SELECT id, title, slug FROM cms_pages WHERE status = 'published' ORDER BY sort_order LIMIT 20",
    ),
    (
        "admin_sessions_expiry_index",
        "SELECT session_id, expires_at FROM admin_sessions ORDER BY expires_at LIMIT 20",
    ),
]


def utc_now():
    """Return an ISO timestamp for audit records."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def open_readonly(database_path):
    """Open SQLite database in read-only mode."""
    path = Path(database_path).resolve()
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def measure_query(connection, name, sql, slow_threshold_ms):
    """Measure one SQLite query."""
    start = time.perf_counter()
    rows = connection.execute(sql).fetchall()
    elapsed_ms = (time.perf_counter() - start) * 1000
    return {
        "name": name,
        "elapsed_ms": round(elapsed_ms, 4),
        "row_count": len(rows),
        "slow": elapsed_ms > slow_threshold_ms,
    }


def run_database_check(database_path=None, report_path=None, json_path=None, dashboard_path=None, slow_threshold_ms=25.0):
    """Run representative read-only database performance checks."""
    db_path = Path(database_path or DEFAULT_DATABASE)
    results = []
    errors = []
    start = time.perf_counter()
    with open_readonly(db_path) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        for name, sql in QUERIES:
            try:
                results.append(measure_query(connection, name, sql, slow_threshold_ms))
            except sqlite3.Error as exc:
                errors.append({"query": name, "error": str(exc)})

    elapsed_ms = (time.perf_counter() - start) * 1000
    slow_queries = [item for item in results if item["slow"]]
    payload = {
        "phase": "12.2",
        "created_at": utc_now(),
        "database": str(db_path),
        "database_engine": "SQLite",
        "database_schema_changed": False,
        "production_modified": False,
        "query_count": len(results),
        "slow_threshold_ms": slow_threshold_ms,
        "slow_query_count": len(slow_queries),
        "average_query_ms": round(sum(item["elapsed_ms"] for item in results) / len(results), 4) if results else 0,
        "max_query_ms": round(max((item["elapsed_ms"] for item in results), default=0), 4),
        "total_elapsed_ms": round(elapsed_ms, 4),
        "sqlite_integrity_check": integrity,
        "queries": results,
        "errors": errors,
        "status": "DATABASE_PERFORMANCE_BASELINE_COMPLETE" if not errors else "DATABASE_PERFORMANCE_CHECK_FAILED",
    }

    report = Path(report_path or DEFAULT_REPORT)
    output_json = Path(json_path or DEFAULT_JSON)
    dashboard = Path(dashboard_path or DEFAULT_DASHBOARD)
    report.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    dashboard.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    report.write_text(render_database_report(payload), encoding="utf-8")
    dashboard.write_text(render_dashboard_report(payload), encoding="utf-8")
    payload["artifacts"] = {
        "markdown": str(report),
        "json": str(output_json),
        "dashboard": str(dashboard),
    }
    output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def load_api_result():
    """Load API benchmark result when available."""
    if not DEFAULT_API_RESULT.exists():
        return None
    return json.loads(DEFAULT_API_RESULT.read_text(encoding="utf-8"))


def render_database_report(payload):
    """Render database report as Markdown."""
    rows = "\n".join(
        f"| `{item['name']}` | `{item['elapsed_ms']}` | `{item['row_count']}` | `{item['slow']}` |"
        for item in payload["queries"]
    )
    return f"""# Phase 12.2 Database Performance Report

## Summary

| Item | Value |
| --- | --- |
| Status | `{payload["status"]}` |
| Database engine | `{payload["database_engine"]}` |
| Query count | `{payload["query_count"]}` |
| Average query ms | `{payload["average_query_ms"]}` |
| Max query ms | `{payload["max_query_ms"]}` |
| Slow query count | `{payload["slow_query_count"]}` |
| SQLite integrity check | `{payload["sqlite_integrity_check"]}` |

## Query Results

| Query | Elapsed ms | Rows | Slow |
| --- | --- | --- | --- |
{rows}

## Safety

| Item | Value |
| --- | --- |
| Production modified | `{payload["production_modified"]}` |
| Database schema changed | `{payload["database_schema_changed"]}` |

## Result

`{payload["status"]}`
"""


def render_dashboard_report(database_payload):
    """Render Phase 12.2 performance dashboard report."""
    api = load_api_result() or {}
    api_status = api.get("status", "API_BENCHMARK_NOT_RUN")
    api_avg = api.get("average_latency_ms", "N/A")
    api_p95 = api.get("p95_latency_ms", "N/A")
    api_p99 = api.get("p99_latency_ms", "N/A")
    api_throughput = api.get("throughput_requests_per_second", "N/A")
    api_errors = api.get("error_rate", "N/A")
    final_status = (
        "PERFORMANCE_BASELINE_COMPLETE"
        if api_status in {"API_BENCHMARK_COMPLETE", "API_BENCHMARK_COMPLETE_WITH_ERRORS"}
        and database_payload["status"] == "DATABASE_PERFORMANCE_BASELINE_COMPLETE"
        else "PERFORMANCE_TEST_BLOCKED"
    )

    bottlenecks = [
        "No production latency baseline exists yet.",
        "SQLite read-only database remains the current data source.",
        "No API caching layer is enabled in the Django replacement API.",
        "Docker deployment still starts the legacy backend by default.",
    ]
    return f"""# Phase 12.2 Performance Report

## Environment

| Item | Value |
| --- | --- |
| API test mode | `LOCAL_DJANGO_TEST_CLIENT` |
| Database | `SQLite read-only baseline` |
| Production modified | `False` |
| Database schema changed | `False` |

## Test Scenarios

- Health endpoints
- GET business APIs
- POST write-intent APIs
- Authentication compatibility endpoints
- SQLite representative read queries
- Local threaded load-test helper

## API Results

| Metric | Value |
| --- | --- |
| Status | `{api_status}` |
| Average latency ms | `{api_avg}` |
| P95 latency ms | `{api_p95}` |
| P99 latency ms | `{api_p99}` |
| Throughput requests/sec | `{api_throughput}` |
| Error rate | `{api_errors}` |

## Database Results

| Metric | Value |
| --- | --- |
| Status | `{database_payload["status"]}` |
| Average query ms | `{database_payload["average_query_ms"]}` |
| Max query ms | `{database_payload["max_query_ms"]}` |
| Slow query count | `{database_payload["slow_query_count"]}` |
| Integrity check | `{database_payload["sqlite_integrity_check"]}` |

## Bottlenecks

{chr(10).join(f"- {item}" for item in bottlenecks)}

## Recommendations

- Add production-like load testing after monitoring is available.
- Add endpoint-level latency metrics.
- Add caching only after repeated slow endpoints are confirmed.
- Review SQLite-to-PostgreSQL performance before production database ownership.

## Final Status

`{final_status}`
"""


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 12.2 database performance check")
    parser.add_argument("--database", default=None, help="SQLite database path.")
    parser.add_argument("--report", default=None, help="Markdown report path.")
    parser.add_argument("--json", default=None, help="JSON report path.")
    parser.add_argument("--dashboard", default=None, help="Dashboard report path.")
    parser.add_argument("--slow-threshold-ms", type=float, default=25.0, help="Slow query threshold in milliseconds.")
    args = parser.parse_args()

    result = run_database_check(
        database_path=args.database,
        report_path=args.report,
        json_path=args.json,
        dashboard_path=args.dashboard,
        slow_threshold_ms=args.slow_threshold_ms,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "DATABASE_PERFORMANCE_BASELINE_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
