"""Kiểm tra readiness trước khi tắt hệ thống legacy ở Phase 11.

Script này cố ý chỉ kiểm tra điều kiện và in báo cáo JSON. Nó không tắt
service, không xóa database, không xóa backup và không di chuyển source code.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_REPORT = PROJECT_ROOT / "docs" / "migration" / "LEGACY_SHUTDOWN_DECISION_REPORT.md"

# Các cờ này đại diện cho bằng chứng vận hành ngoài đời thực.
# Nếu thiếu một cờ, Phase 11 phải dừng an toàn.
REQUIRED_SHUTDOWN_FLAGS = {
    "PHASE11_TRAFFIC_MIGRATION_VERIFIED": "traffic đã chuyển sang Django",
    "PHASE11_ZERO_LEGACY_TRAFFIC_CONFIRMED": "không còn traffic vào legacy",
    "PHASE11_ROLLBACK_WINDOW_CLOSED": "cửa sổ rollback đã kết thúc",
    "PHASE11_ARCHIVE_RESTORE_VERIFIED": "archive có thể restore lại",
    "PHASE11_BUSINESS_OWNER_APPROVED": "business owner đã duyệt",
}

# Các thành phần legacy cần tồn tại cho tới khi được duyệt shutdown cuối cùng.
LEGACY_ASSETS = {
    "legacy_entrypoint": PROJECT_ROOT / "backend" / "app.py",
    "legacy_database": PROJECT_ROOT / "backend" / "database" / "mecprecision.sqlite",
    "legacy_schema": PROJECT_ROOT / "backend" / "database" / "schema.sql",
    "legacy_seed": PROJECT_ROOT / "backend" / "database" / "seed.sql",
}


def flag_enabled(value):
    """Trả về True khi cờ vận hành được bật rõ ràng."""
    return str(value or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "passed",
        "approved",
        "completed",
        "verified",
    }


def read_text(path):
    """Đọc file text, nếu file không tồn tại thì trả chuỗi rỗng để chặn an toàn."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def evaluate_required_flags(env):
    """Kiểm tra từng cờ bắt buộc và gom lỗi còn thiếu."""
    checks = {}
    errors = []
    for key, label in REQUIRED_SHUTDOWN_FLAGS.items():
        passed = flag_enabled(env.get(key))
        checks[key] = {
            "label": label,
            "passed": passed,
        }
        if not passed:
            errors.append(f"Missing shutdown evidence: {label} ({key}).")
    return checks, errors


def evaluate_decision_report(decision_report_path=DEFAULT_DECISION_REPORT):
    """Đọc báo cáo Phase 10.6 để biết Phase 11 có được phép tiếp tục chưa."""
    content = read_text(decision_report_path)
    allow_phase_11 = "ALLOW_PHASE_11" in content
    keep_legacy_active = "KEEP_LEGACY_ACTIVE" in content or "DO NOT START PHASE 11" in content
    report_exists = Path(decision_report_path).exists()
    errors = []

    if not report_exists:
        errors.append("Missing legacy shutdown decision report.")
    if keep_legacy_active:
        errors.append("Phase 10.6 decision requires KEEP_LEGACY_ACTIVE.")
    if not allow_phase_11:
        errors.append("Architecture approval marker ALLOW_PHASE_11 is missing.")

    return {
        "path": str(decision_report_path),
        "exists": report_exists,
        "allow_phase_11": allow_phase_11,
        "keep_legacy_active": keep_legacy_active,
        "errors": errors,
    }


def inspect_legacy_assets():
    """Kiểm tra các asset legacy vẫn còn để phục vụ rollback/archive."""
    assets = {}
    errors = []
    for name, path in LEGACY_ASSETS.items():
        exists = path.exists()
        assets[name] = {
            "path": str(path),
            "exists": exists,
            "size_bytes": path.stat().st_size if exists and path.is_file() else None,
        }
        if not exists:
            errors.append(f"Missing required legacy archive asset: {name}.")
    return assets, errors


def evaluate_shutdown_readiness(env=None, decision_report_path=DEFAULT_DECISION_REPORT):
    """Tổng hợp toàn bộ điều kiện để quyết định có thể shutdown legacy chưa."""
    started_at = time.perf_counter()
    env = env or os.environ
    decision = evaluate_decision_report(decision_report_path)
    flag_checks, flag_errors = evaluate_required_flags(env)
    assets, asset_errors = inspect_legacy_assets()
    errors = list(decision["errors"]) + flag_errors + asset_errors
    ready = not errors

    return {
        "status": "ready_for_manual_shutdown_review" if ready else "blocked_safely",
        "legacy_shutdown_recommendation": "ALLOW_MANUAL_SHUTDOWN_REVIEW" if ready else "KEEP_LEGACY_ACTIVE",
        "legacy_shutdown_executed": False,
        "legacy_code_removed": False,
        "legacy_database_deleted": False,
        "backups_deleted": False,
        "traffic_switch_executed": False,
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
        "decision_report": decision,
        "shutdown_flags": flag_checks,
        "legacy_assets": assets,
        "errors": errors,
    }


def main():
    """CLI entrypoint cho kiểm tra readiness Phase 11."""
    # PowerShell trên Windows có thể dùng codepage không hỗ trợ đủ tiếng Việt.
    # Reconfigure stdout giúp JSON tiếng Việt in ra ổn định hơn.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11 legacy shutdown readiness gate")
    parser.add_argument(
        "--decision-report",
        default=str(DEFAULT_DECISION_REPORT),
        help="Đường dẫn tới báo cáo quyết định shutdown legacy.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Trả mã lỗi khác 0 nếu shutdown bị chặn. Mặc định chặn an toàn vẫn exit 0.",
    )
    args = parser.parse_args()
    result = evaluate_shutdown_readiness(decision_report_path=Path(args.decision_report))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "ready_for_manual_shutdown_review":
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
