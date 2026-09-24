"""Validate AI Phase Review Engine requirements.

The validator checks required files, required tests, generated outputs, and
forbidden safety violations. It never modifies project code.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "ai-review" / "config.yml"
DEFAULT_EVIDENCE = PROJECT_ROOT / "ai-review" / "evidence" / "current_phase.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "ai-review" / "results" / "rule_validation.json"


def utc_now():
    """Return an ISO timestamp for validation evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_simple_config(path=DEFAULT_CONFIG):
    """Parse the small YAML subset used by `ai-review/config.yml`."""
    config = {
        "required_files": [],
        "ignored_files": [],
        "security_rules": {},
        "ollama": {},
    }
    current = None
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith(":") and not line.startswith("-"):
            current = line[:-1]
            continue
        if line.startswith("- ") and current in {"required_files", "ignored_files", "required_checks"}:
            config.setdefault(current, []).append(line[2:].strip())
            continue
        if ":" in line and current in {"security_rules", "ollama"}:
            key, value = [part.strip() for part in line.split(":", 1)]
            if value.lower() == "true":
                parsed = True
            elif value.lower() == "false":
                parsed = False
            else:
                parsed = value
            config[current][key] = parsed
    return config


def load_json(path):
    """Load JSON file if available."""
    target = Path(path)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def file_status(relative_path):
    """Return existence details for one project-relative path."""
    target = PROJECT_ROOT / relative_path
    return {
        "path": relative_path,
        "exists": target.exists(),
        "size_bytes": target.stat().st_size if target.exists() else 0,
    }


def validate_requirements(config_path=DEFAULT_CONFIG, evidence_path=DEFAULT_EVIDENCE, output_path=None):
    """Validate configured requirements and write JSON result."""
    config = parse_simple_config(config_path)
    evidence = load_json(evidence_path)
    missing = []
    warnings = []
    checked_files = []

    for relative_path in config.get("required_files", []):
        status = file_status(relative_path)
        checked_files.append(status)
        if not status["exists"]:
            missing.append(relative_path)
        elif status["size_bytes"] == 0:
            warnings.append(f"Empty file: {relative_path}")

    safety = evidence.get("safety", {})
    security_rules = config.get("security_rules", {})
    forbidden_changes = []
    if safety.get("production_approved") and not security_rules.get("production_approval_allowed", False):
        forbidden_changes.append("AI attempted to approve production.")
    if safety.get("code_modified_by_ai") and not security_rules.get("code_auto_modify_allowed", False):
        forbidden_changes.append("AI attempted to modify code.")
    if safety.get("failed_tests_skipped") and not security_rules.get("failed_test_bypass_allowed", False):
        forbidden_changes.append("Failed tests were bypassed.")
    if safety.get("external_ai_used") and not security_rules.get("external_ai_allowed", False):
        forbidden_changes.append("External AI was used.")

    required_outputs = {
        "evidence_file": Path(evidence_path).exists(),
        "config_file": Path(config_path).exists(),
    }
    if not required_outputs["evidence_file"]:
        missing.append(str(Path(evidence_path).relative_to(PROJECT_ROOT)))

    status = "PASS" if not missing and not forbidden_changes else "FAIL"
    result = {
        "phase": evidence.get("phase", "unknown"),
        "created_at": utc_now(),
        "status": status,
        "missing": missing,
        "warnings": warnings,
        "checked_files": checked_files,
        "required_outputs": required_outputs,
        "forbidden_changes": forbidden_changes,
        "safety": {
            "production_approval_allowed": False,
            "code_auto_modify_allowed": False,
            "failed_test_bypass_allowed": False,
            "human_approval_required": True,
        },
    }

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    """Command-line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Validate AI review requirements.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--evidence", default=str(DEFAULT_EVIDENCE))
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    result = validate_requirements(config_path=args.config, evidence_path=args.evidence, output_path=args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
