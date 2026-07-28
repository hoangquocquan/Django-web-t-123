"""Collect evidence for the AI Phase Review Engine.

The collector reads project files and Git metadata only. It does not modify
code, approve production, or call external services.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "ai-review" / "evidence" / "current_phase.json"


def utc_now():
    """Return an ISO timestamp for evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_git(args):
    """Run a read-only Git command."""
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def read_text(path, limit=12000):
    """Read a text file with a limit so prompts stay compact."""
    target = Path(path)
    if not target.exists():
        return ""
    return target.read_text(encoding="utf-8", errors="replace")[:limit]


def find_phase_requirement(phase):
    """Find the saved Codex prompt for a phase."""
    prompt_dir = PROJECT_ROOT / "docs" / "codex-prompts"
    matches = sorted(prompt_dir.glob(f"PHASE_{phase}*.md"))
    return matches[0] if matches else None


def list_existing(paths):
    """Return existing files from a list of candidate paths."""
    result = []
    for path in paths:
        target = PROJECT_ROOT / path
        if target.exists():
            result.append(
                {
                    "path": path,
                    "size_bytes": target.stat().st_size,
                    "content_preview": read_text(target, limit=3000),
                }
            )
    return result


def collect_evidence(phase="13.5", output_path=None):
    """Collect phase evidence and write JSON output."""
    requirement_path = find_phase_requirement(phase)
    changed_files = run_git(["status", "--short"])["stdout"]
    diff_files = run_git(["diff", "--name-only", "HEAD"])["stdout"]
    branch = run_git(["branch", "--show-current"])["stdout"]
    commit = run_git(["rev-parse", "HEAD"])["stdout"]
    latest_commit = run_git(["log", "-1", "--oneline"])["stdout"]

    generated_reports = list_existing(
        [
            "docs/cicd/test_pipeline_result.json",
            "docs/docker/docker_build_report.json",
            "docs/deployment/deployment_result.json",
            "docs/deployment/health_result.json",
            "docs/deployment/rollback_result.json",
            "docs/n8n/n8n_execution_report.json",
            "docs/ai-devops/N8N_AI_REVIEW_REPORT.md",
            "docs/reviews/PHASE_13.4_DEPLOYMENT_REPORT.md",
        ]
    )
    logs = list_existing(
        [
            "docs/ai-devops/phase_validation_result.json",
            "docs/cicd/test_pipeline_result.json",
            "docs/deployment/health_result.json",
        ]
    )

    evidence = {
        "phase": phase,
        "created_at": utc_now(),
        "requirement_file": str(requirement_path.relative_to(PROJECT_ROOT)) if requirement_path else "",
        "requirement_text": read_text(requirement_path) if requirement_path else "",
        "git": {
            "branch": branch,
            "commit": commit,
            "latest_commit": latest_commit,
            "changed_files": changed_files.splitlines() if changed_files else [],
            "diff_files": diff_files.splitlines() if diff_files else [],
        },
        "generated_reports": generated_reports,
        "logs": logs,
        "safety": {
            "production_approved": False,
            "code_modified_by_ai": False,
            "failed_tests_skipped": False,
            "external_ai_used": False,
            "human_approval_required": True,
        },
    }

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    return evidence


def main():
    """Command-line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Collect phase evidence for AI review.")
    parser.add_argument("--phase", default="13.5")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    result = collect_evidence(phase=args.phase, output_path=args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
