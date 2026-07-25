"""Kiểm tra readiness trước khi decommission legacy API ở Phase 11.1.

Script này chỉ đánh giá điều kiện an toàn. Nó không sửa `backend/app.py`,
không tắt route legacy và không thay đổi proxy/nginx.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Danh sách route legacy được lấy từ `backend/app.py` và OpenAPI legacy.
# `replacement_ready=False` nghĩa là chưa được phép decommission route đó.
LEGACY_API_ROUTES = [
    {
        "method": "GET",
        "legacy_path": "/api/health",
        "django_replacement": "/api/v1/health/",
        "replacement_ready": True,
        "notes": "Health endpoint đã có contract test tương thích.",
    },
    {
        "method": "GET",
        "legacy_path": "/api/products",
        "django_replacement": "/api/v1/catalog/products/",
        "replacement_ready": True,
        "notes": "Django có read-only catalog products API.",
    },
    {
        "method": "GET",
        "legacy_path": "/api/products/{id}",
        "django_replacement": "/api/v1/catalog/products/{id}/",
        "replacement_ready": True,
        "notes": "Django có read-only product detail API.",
    },
    {
        "method": "GET",
        "legacy_path": "/api/product-categories",
        "django_replacement": "/api/v1/catalog/categories/",
        "replacement_ready": True,
        "notes": "Django có read-only catalog categories API.",
    },
    {
        "method": "GET",
        "legacy_path": "/api/news",
        "django_replacement": None,
        "replacement_ready": False,
        "notes": "Chưa có Django news API tương đương.",
    },
    {
        "method": "GET",
        "legacy_path": "/api/home",
        "django_replacement": None,
        "replacement_ready": False,
        "notes": "Chưa có Django home aggregate API tương đương.",
    },
    {
        "method": "GET",
        "legacy_path": "/api/capabilities",
        "django_replacement": None,
        "replacement_ready": False,
        "notes": "Chưa có Django capabilities API tương đương.",
    },
    {
        "method": "GET",
        "legacy_path": "/api/openapi.json",
        "django_replacement": None,
        "replacement_ready": False,
        "notes": "Chưa có OpenAPI schema Django thay thế trong project này.",
    },
    {
        "method": "GET",
        "legacy_path": "/api/version",
        "django_replacement": None,
        "replacement_ready": False,
        "notes": "Chưa có Django API version endpoint tương đương.",
    },
    {
        "method": "GET",
        "legacy_path": "/api/aws-demo",
        "django_replacement": None,
        "replacement_ready": False,
        "notes": "Demo endpoint legacy, chưa migrate sang Django.",
    },
    {
        "method": "GET",
        "legacy_path": "/api/external/weather",
        "django_replacement": None,
        "replacement_ready": False,
        "notes": "External API demo chưa migrate sang Django.",
    },
    {
        "method": "POST",
        "legacy_path": "/api/contact",
        "django_replacement": "/api/v1/crm/contact-requests/",
        "replacement_ready": False,
        "notes": "Django hiện chỉ read-only, chưa thay thế write contract.",
    },
    {
        "method": "POST",
        "legacy_path": "/api/quote-request",
        "django_replacement": "/api/v1/sales/quotes/",
        "replacement_ready": False,
        "notes": "Django hiện chỉ read-only, chưa thay thế quote request write contract.",
    },
    {
        "method": "POST",
        "legacy_path": "/api/ai/chat",
        "django_replacement": None,
        "replacement_ready": False,
        "notes": "AI chatbot API chưa migrate sang Django.",
    },
    {
        "method": "POST/PUT/DELETE",
        "legacy_path": "/api/products",
        "django_replacement": None,
        "replacement_ready": False,
        "notes": "Django business APIs Phase 9.1 vẫn chặn write methods.",
    },
]

REQUIRED_FLAGS = {
    "PHASE11_1_DJANGO_API_CONTRACTS_VERIFIED": "Django API contracts pass in production",
    "PHASE11_1_ZERO_LEGACY_API_TRAFFIC_CONFIRMED": "traffic logs prove no clients use legacy routes",
    "PHASE11_1_CLIENT_CONTRACT_TESTS_PASSED": "client contract tests passed",
    "PHASE11_1_ROLLBACK_WINDOW_RESPECTED": "rollback window is still respected",
    "PHASE11_1_ACCESS_LOGS_ARCHIVED": "legacy API access logs are archived",
}


def flag_enabled(value):
    """Trả về True khi một cờ vận hành được bật rõ ràng."""
    return str(value or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "passed",
        "approved",
        "completed",
        "verified",
    }


def evaluate_required_flags(env):
    """Kiểm tra các bằng chứng bắt buộc trước khi decommission API."""
    checks = {}
    errors = []
    for key, label in REQUIRED_FLAGS.items():
        passed = flag_enabled(env.get(key))
        checks[key] = {
            "label": label,
            "passed": passed,
        }
        if not passed:
            errors.append(f"Missing API decommission evidence: {label} ({key}).")

    approval_id = str(env.get("PHASE11_1_DECOMMISSION_APPROVAL_ID") or "").strip()
    checks["PHASE11_1_DECOMMISSION_APPROVAL_ID"] = {
        "label": "architecture/business approval id",
        "passed": bool(approval_id),
        "value": approval_id or None,
    }
    if not approval_id:
        errors.append("Missing API decommission approval id (PHASE11_1_DECOMMISSION_APPROVAL_ID).")
    return checks, errors


def analyze_route_mapping(routes=None):
    """Tìm các route legacy chưa có replacement Django đủ an toàn."""
    routes = routes or LEGACY_API_ROUTES
    missing = [
        route
        for route in routes
        if not route["replacement_ready"]
    ]
    return {
        "total_legacy_routes": len(routes),
        "replacement_ready_count": len(routes) - len(missing),
        "not_ready_count": len(missing),
        "not_ready_routes": missing,
        "routes": routes,
    }


def inspect_traffic_log(log_path):
    """Đọc log traffic nếu operator cung cấp và tìm request vào `/api/` legacy."""
    if not log_path:
        return {
            "provided": False,
            "path": None,
            "legacy_api_hits": None,
            "sample_hits": [],
            "errors": ["Traffic log path was not provided."],
        }

    path = Path(log_path)
    if not path.exists():
        return {
            "provided": True,
            "path": str(path),
            "legacy_api_hits": None,
            "sample_hits": [],
            "errors": ["Traffic log path does not exist."],
        }

    hits = []
    with path.open("r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            # `/api/v1/` là namespace Django mới, không phải legacy API.
            # Ở đây chỉ coi `/api/...` không thuộc `/api/v1/...` là traffic legacy.
            if "/api/" in line and "/api/v1/" not in line:
                hits.append(line.strip())
                if len(hits) >= 10:
                    break

    return {
        "provided": True,
        "path": str(path),
        "legacy_api_hits": len(hits),
        "sample_hits": hits,
        "errors": [] if not hits else ["Traffic log still contains legacy API hits."],
    }


def evaluate_api_decommission_readiness(env=None, routes=None):
    """Tổng hợp điều kiện để biết có thể decommission legacy API chưa."""
    started_at = time.perf_counter()
    env = env or os.environ
    flags, flag_errors = evaluate_required_flags(env)
    mapping = analyze_route_mapping(routes)
    traffic = inspect_traffic_log(env.get("PHASE11_1_LEGACY_TRAFFIC_LOG"))

    errors = list(flag_errors)
    if mapping["not_ready_routes"]:
        errors.append("Some legacy API routes do not have verified Django replacements.")
    errors.extend(traffic["errors"])

    ready = not errors
    return {
        "status": "ready_for_manual_decommission_review" if ready else "blocked_safely",
        "legacy_api_decommission_recommendation": (
            "ALLOW_MANUAL_DECOMMISSION_REVIEW" if ready else "KEEP_LEGACY_API_ACTIVE"
        ),
        "legacy_routes_disabled": False,
        "legacy_routes_removed": False,
        "compatibility_adapters_removed": False,
        "proxy_changes_applied": False,
        "database_changed": False,
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
        "required_flags": flags,
        "route_mapping": mapping,
        "traffic_verification": traffic,
        "errors": errors,
    }


def main():
    """CLI entrypoint cho Phase 11.1 legacy API decommission gate."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1 legacy API decommission readiness")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Trả mã lỗi khác 0 nếu decommission bị chặn. Mặc định chặn an toàn vẫn exit 0.",
    )
    args = parser.parse_args()
    result = evaluate_api_decommission_readiness()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "ready_for_manual_decommission_review":
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
