"""Phase 12.1 offline dependency security audit.

The audit is intentionally offline. It does not call package indexes or CVE
services, so it cannot claim a complete vulnerability scan. It records package
pinning, installed versions and local policy warnings for review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUIREMENT_FILES = [
    PROJECT_ROOT / "backend" / "requirements.txt",
    PROJECT_ROOT / "django_backend" / "requirements.txt",
]
DEFAULT_REPORT_PATH = PROJECT_ROOT / "docs" / "reviews" / "PHASE_12.1_DEPENDENCY_AUDIT_REPORT.md"
DEFAULT_JSON_PATH = PROJECT_ROOT / "docs" / "reviews" / "PHASE_12.1_DEPENDENCY_AUDIT_REPORT.json"

STRICT_PIN_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+==[^=<>!~]+$")
PACKAGE_NAME_PATTERN = re.compile(r"^([A-Za-z0-9_.-]+)")

LOCAL_SECURITY_NOTES = {
    "django": "Keep on an actively supported Django release and apply security updates quickly.",
    "djangorestframework": "Review API authentication, throttling and permission settings before public exposure.",
    "django-cors-headers": "Keep CORS_ALLOWED_ORIGINS explicit; do not use wildcard origins in production.",
    "python-dotenv": "Do not commit real .env files; load production secrets from a secret manager.",
    "pypdf": "Treat uploaded PDFs as untrusted input and scan/limit file size before processing.",
    "psycopg": "Use TLS and credential rotation for PostgreSQL production connections.",
    "pytest": "Test-only dependency; do not install in minimal production image unless needed.",
    "pytest-django": "Test-only dependency; do not install in minimal production image unless needed.",
}


def utc_now():
    """Return an ISO timestamp for audit records."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_name(name):
    """Normalize a Python package name for comparison."""
    return str(name or "").strip().lower().replace("_", "-")


def read_requirement_lines(path):
    """Read requirement lines and ignore comments or blank lines."""
    requirement_path = Path(path)
    if not requirement_path.exists():
        return []
    lines = []
    for line in requirement_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            lines.append(stripped)
    return lines


def package_name_from_requirement(requirement):
    """Extract the package name from a requirement string."""
    match = PACKAGE_NAME_PATTERN.match(requirement)
    return normalize_name(match.group(1) if match else requirement)


def installed_version(package_name):
    """Return installed version or NOT_INSTALLED."""
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return "NOT_INSTALLED"


def classify_requirement(requirement):
    """Classify one dependency line."""
    name = package_name_from_requirement(requirement)
    pinned = bool(STRICT_PIN_PATTERN.match(requirement))
    version = installed_version(name)
    warnings = []

    if not pinned:
        warnings.append("Dependency is not strictly pinned with ==.")
    if version == "NOT_INSTALLED":
        warnings.append("Dependency is not installed in the current Python environment.")
    note = LOCAL_SECURITY_NOTES.get(name)
    if note:
        warnings.append(note)

    return {
        "requirement": requirement,
        "package": name,
        "installed_version": version,
        "strictly_pinned": pinned,
        "known_vulnerability_status": "NOT_CHECKED_OFFLINE",
        "warnings": warnings,
    }


def collect_dependencies(requirement_files=None):
    """Collect dependencies from requirement files."""
    dependencies = []
    for path in requirement_files or DEFAULT_REQUIREMENT_FILES:
        requirement_path = Path(path)
        for requirement in read_requirement_lines(requirement_path):
            item = classify_requirement(requirement)
            item["source_file"] = str(requirement_path)
            dependencies.append(item)
    return dependencies


def build_audit(requirement_files=None):
    """Build the dependency audit payload."""
    dependencies = collect_dependencies(requirement_files)
    unpinned = [item for item in dependencies if not item["strictly_pinned"]]
    missing = [item for item in dependencies if item["installed_version"] == "NOT_INSTALLED"]
    status = "DEPENDENCY_AUDIT_COMPLETE_WITH_WARNINGS" if unpinned or missing else "DEPENDENCY_AUDIT_COMPLETE"

    return {
        "phase": "12.1",
        "created_at": utc_now(),
        "status": status,
        "scanner_mode": "OFFLINE_STATIC_REQUIREMENTS_AUDIT",
        "cve_scan_status": "NOT_RUN_NETWORK_DISABLED",
        "dependency_count": len(dependencies),
        "unpinned_count": len(unpinned),
        "missing_installed_count": len(missing),
        "dependencies": dependencies,
        "recommendations": [
            "Pin production dependencies with exact versions or a locked requirements file.",
            "Run pip-audit, Safety, Dependabot or GitHub Advanced Security in CI before production.",
            "Separate production dependencies from test/development dependencies.",
            "Review CORS, authentication and throttling before public API exposure.",
        ],
    }


def render_report(audit):
    """Render the dependency audit as Markdown."""
    rows = []
    for item in audit["dependencies"]:
        warning_text = "<br>".join(item["warnings"]) if item["warnings"] else "None"
        rows.append(
            "| `{package}` | `{requirement}` | `{installed}` | `{pinned}` | `{vuln}` | {warnings} |".format(
                package=item["package"],
                requirement=item["requirement"],
                installed=item["installed_version"],
                pinned=item["strictly_pinned"],
                vuln=item["known_vulnerability_status"],
                warnings=warning_text,
            )
        )

    return """# Phase 12.1 Dependency Audit Report

## Scope

Offline dependency audit for Python requirement files. This report does not use
internet access and therefore does not replace a real CVE scan.

## Summary

| Item | Value |
| --- | --- |
| Status | `{status}` |
| Scanner mode | `{scanner_mode}` |
| CVE scan status | `{cve_status}` |
| Dependency count | `{dependency_count}` |
| Unpinned dependency count | `{unpinned_count}` |
| Missing installed count | `{missing_count}` |

## Dependencies

| Package | Requirement | Installed | Strictly pinned | Known vulnerability status | Warnings |
| --- | --- | --- | --- | --- | --- |
{rows}

## Recommendations

{recommendations}

## Final Result

`{status}`
""".format(
        status=audit["status"],
        scanner_mode=audit["scanner_mode"],
        cve_status=audit["cve_scan_status"],
        dependency_count=audit["dependency_count"],
        unpinned_count=audit["unpinned_count"],
        missing_count=audit["missing_installed_count"],
        rows="\n".join(rows),
        recommendations="\n".join(f"- {item}" for item in audit["recommendations"]),
    )


def write_report(audit, report_path=None, json_path=None):
    """Write Markdown and JSON audit artifacts."""
    report = Path(report_path or DEFAULT_REPORT_PATH)
    payload = Path(json_path or DEFAULT_JSON_PATH)
    report.parent.mkdir(parents=True, exist_ok=True)
    payload.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(audit), encoding="utf-8")
    payload.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"markdown": str(report), "json": str(payload)}


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 12.1 offline dependency audit")
    parser.add_argument("--report", default=None, help="Markdown report output path.")
    parser.add_argument("--json", default=None, help="JSON report output path.")
    args = parser.parse_args()

    audit = build_audit()
    audit["artifacts"] = write_report(audit, report_path=args.report, json_path=args.json)
    print(json.dumps(audit, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
