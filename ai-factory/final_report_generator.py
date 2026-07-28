"""Generate the final AI Software Factory review report."""

from __future__ import annotations

import json
from pathlib import Path


FACTORY_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FACTORY_DIR.parents[0]
DEFAULT_EVIDENCE = FACTORY_DIR / "evidence" / "package.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "reviews" / "AI_SOFTWARE_FACTORY_REPORT.md"


def load_evidence(path=None):
    """Load the unified evidence package."""
    target = Path(path or DEFAULT_EVIDENCE)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def summarize_commands(commands):
    """Render command status lines for the report."""
    if not commands:
        return "- No command evidence recorded."
    return "\n".join(
        f"- `{item.get('command', '')}`: {item.get('status', 'UNKNOWN')}"
        for item in commands
    )


def final_decision(evidence):
    """Decide whether the phase is ready for human review."""
    commands = evidence.get("tests", [])
    all_passed = all(item.get("status") == "PASS" for item in commands) if commands else False
    ai_review = evidence.get("ai_review", {})
    ai_status = ai_review.get("status", "UNKNOWN")
    if all_passed and ai_status not in {"BLOCKED", "FAIL"}:
        return "WAITING_FOR_HUMAN_APPROVAL"
    return "BLOCKED_FOR_FIX"


def render_report(evidence):
    """Render the AI Software Factory Markdown report."""
    correction = evidence.get("factory_correction") or evidence.get("correction_history", {})
    ai_review = evidence.get("ai_review", {})
    decision = final_decision(evidence)
    return f"""# AI Software Factory Report

## Phase

```text
{evidence.get("phase", "UNKNOWN")}
```

## Implementation Result

```text
{decision}
```

## Test Result

{summarize_commands(evidence.get("tests", []))}

## Correction History

Status:

```text
{correction.get("status", "NOT_RUN")}
```

Final decision:

```text
{correction.get("final_decision", correction.get("reason", "NOT_RUN"))}
```

## Ollama Evaluation

Status:

```text
{ai_review.get("status", "UNKNOWN")}
```

Decision:

```text
{ai_review.get("decision", "UNKNOWN")}
```

## Evidence Package

```text
ai-factory/evidence/package.json
```

## Safety

- Production deployed: false
- Code auto merged: false
- Human approval bypassed: false
- Failed tests hidden: false
- Human approval required: true

## Final Decision

```text
{decision}
```
"""


def generate_final_report(evidence_path=None, output_path=None):
    """Generate and write the final review report."""
    evidence = load_evidence(evidence_path)
    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(evidence), encoding="utf-8")
    try:
        display_output = str(output.relative_to(PROJECT_ROOT))
    except ValueError:
        display_output = str(output)
    return {
        "output": display_output,
        "decision": final_decision(evidence),
    }
