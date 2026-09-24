"""Build one evidence package for the AI Software Factory workflow."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


FACTORY_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FACTORY_DIR.parents[0]
DEFAULT_OUTPUT = FACTORY_DIR / "evidence" / "package.json"


def utc_now():
    """Return an ISO timestamp for evidence records."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_git(args):
    """Read Git metadata without changing repository state."""
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip()


def load_json(path):
    """Load a JSON artifact when it exists."""
    target = Path(path)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def file_summary(path):
    """Return safe file metadata for an evidence artifact."""
    target = PROJECT_ROOT / path
    return {
        "path": path,
        "exists": target.exists(),
        "size_bytes": target.stat().st_size if target.exists() else 0,
    }


def build_evidence_package(phase="13.8", command_results=None, correction_result=None, output_path=None):
    """Collect source changes, tests, logs, AI review, and correction history."""
    commands = command_results or []
    package = {
        "phase": phase,
        "created_at": utc_now(),
        "source_changes": {
            "branch": run_git(["branch", "--show-current"]),
            "commit": run_git(["rev-parse", "HEAD"]),
            "status_short": run_git(["status", "--short"]),
            "diff_stat": run_git(["diff", "--stat"]),
        },
        "tests": commands,
        "logs": [
            {
                "command": item.get("command", ""),
                "status": item.get("status", "UNKNOWN"),
                "stdout_tail": item.get("stdout_tail", ""),
                "stderr_tail": item.get("stderr_tail", ""),
            }
            for item in commands
        ],
        "ai_review": load_json(PROJECT_ROOT / "ai-review" / "results" / "ai_review.json"),
        "factory_correction": correction_result or {
            "status": "NOT_RECORDED",
            "reason": "Factory runner did not provide correction details.",
        },
        "correction_history": load_json(PROJECT_ROOT / "ai-review" / "results" / "self_correction_result.json"),
        "artifacts": [
            file_summary("docs/reviews/PHASE_AI_REVIEW_REPORT.md"),
            file_summary("docs/reviews/PHASE_13.6_SELF_CORRECTION_REPORT.md"),
            file_summary("n8n/results/execution_history.json"),
        ],
        "safety": {
            "production_deployed": False,
            "code_auto_merged": False,
            "human_approval_bypassed": False,
            "failed_tests_hidden": False,
            "human_approval_required": True,
        },
    }

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")
    return package
