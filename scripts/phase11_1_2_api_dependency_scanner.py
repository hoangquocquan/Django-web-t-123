"""Scan source/config files for legacy API dependencies.

The scanner helps find clients that still reference `/api/...` legacy routes.
It excludes `/api/v1/...` because that namespace belongs to Django replacements.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCAN_ROOTS = ["frontend", "scripts"]
TEXT_SUFFIXES = {
    ".py",
    ".js",
    ".html",
    ".css",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".md",
    ".ps1",
}
SKIP_PARTS = {"__pycache__", ".git", "logs", "uploads", "fixtures"}
LEGACY_API_PATTERN = re.compile(r"(?P<path>/api(?:/[A-Za-z0-9._~{}-]+)+)")

REPLACEMENTS = {
    "/api/health": "/api/v1/health/",
    "/api/products": "/api/v1/catalog/products/",
    "/api/products/{id}": "/api/v1/catalog/products/{id}/",
    "/api/product-categories": "/api/v1/catalog/categories/",
    "/api/news": "/api/v1/news/",
    "/api/home": "/api/v1/public/home/",
    "/api/capabilities": "/api/v1/catalog/capabilities/",
    "/api/openapi.json": "/api/v1/openapi.json",
    "/api/version": "/api/v1/version/",
    "/api/aws-demo": "/api/v1/demo/aws/",
    "/api/external/weather": "/api/v1/demo/external/weather/",
    "/api/contact": "/api/v1/crm/contact-requests/",
    "/api/quote-request": "/api/v1/sales/quotes/",
    "/api/ai/chat": "/api/v1/ai/chat/",
}


def is_replacement_path(path):
    """Return True for Django replacement API paths."""
    return path == "/api/v1" or path.startswith("/api/v1/")


def normalize_legacy_path(path):
    """Normalize dynamic legacy paths for mapping lookup."""
    path = path.rstrip(".")
    if re.fullmatch(r"/api/products/\d+", path):
        return "/api/products/{id}"
    return path


def display_path(path):
    """Return a stable path string for reports, even outside the project root."""
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def should_scan(path):
    """Return True when a file is a useful text source for dependency scanning."""
    if any(part in SKIP_PARTS for part in path.parts):
        return False
    return path.suffix.lower() in TEXT_SUFFIXES


def iter_scan_files(scan_roots=None):
    """Yield files under configured roots."""
    roots = scan_roots or DEFAULT_SCAN_ROOTS
    for root in roots:
        root_path = PROJECT_ROOT / root
        if not root_path.exists():
            continue
        if root_path.is_file() and should_scan(root_path):
            yield root_path
            continue
        for path in root_path.rglob("*"):
            if path.is_file() and should_scan(path):
                yield path


def scan_file(path):
    """Scan one file for legacy API references."""
    findings = []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return findings

    for line_number, line in enumerate(content, start=1):
        for match in LEGACY_API_PATTERN.finditer(line):
            path_text = match.group("path").rstrip(".")
            if path_text in {"/api", "/api/"}:
                continue
            if is_replacement_path(path_text):
                continue
            normalized = normalize_legacy_path(path_text)
            findings.append(
                {
                    "file": display_path(path),
                    "line": line_number,
                    "reference": path_text,
                    "normalized_reference": normalized,
                    "replacement": REPLACEMENTS.get(normalized),
                    "replacement_status": "READY" if normalized in REPLACEMENTS else "UNKNOWN",
                }
            )
    return findings


def scan_dependencies(scan_roots=None):
    """Scan configured roots and summarize legacy API dependencies."""
    findings = []
    for path in iter_scan_files(scan_roots):
        findings.extend(scan_file(path))
    unknown = [item for item in findings if item["replacement_status"] == "UNKNOWN"]
    return {
        "status": "passed" if not unknown else "blocked_safely",
        "files_scanned": len(list(iter_scan_files(scan_roots))),
        "legacy_references": len(findings),
        "unknown_references": len(unknown),
        "findings": findings[:200],
        "decision": "DEPENDENCIES_DOCUMENTED" if not unknown else "UNKNOWN_DEPENDENCIES_FOUND",
    }


def parse_roots(values=None, env=None):
    """Read scan roots from CLI or environment."""
    if values:
        return values
    env = env or os.environ
    raw = env.get("PHASE11_1_2_SCAN_ROOTS", "")
    if not raw.strip():
        return DEFAULT_SCAN_ROOTS
    return [part.strip() for part in re.split(r"[;,]", raw) if part.strip()]


def main():
    """CLI entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Phase 11.1.2 API dependency scanner")
    parser.add_argument("--root", action="append", default=[], help="Root folder or file to scan.")
    args = parser.parse_args()
    result = scan_dependencies(parse_roots(args.root))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
