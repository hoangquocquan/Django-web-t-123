# Self Correction Security

## Purpose

The AI self correction loop helps diagnose failed tests and generate a fix task.
It does not modify production and does not hide failing tests.

## Maximum Retry Limit

The retry controller allows at most 3 attempts.

If tests still fail after 3 attempts:

- status stays `BLOCKED`
- errors remain visible
- human review is required

## Human Approval

AI can suggest a fix. Codex or a developer applies the fix. Human approval is
required before final merge.

Human approval is required for the final merge decision.

## No Production Modification

Forbidden actions:

- deploy production automatically
- modify production data
- change production infrastructure
- approve production release

## No Fake PASS

The loop must not:

- skip failed tests
- rewrite failed output
- mark a failed command as passed
- delete error evidence

## Audit Log

Required audit files:

```text
ai-review/results/error_report.json
ai-review/results/error_analysis.json
docs/codex-prompts/AUTO_FIX_TASK.md
docs/reviews/PHASE_13.6_SELF_CORRECTION_REPORT.md
```

## Safety Flags

Every result must record:

- production_modified: false
- tests_skipped: false
- fake_pass_created: false
- human_approval_required: true
