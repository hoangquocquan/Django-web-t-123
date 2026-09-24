# AI Software Factory Guide

## Purpose

The AI Software Factory gives every future engineering phase the same repeatable workflow: define work, implement with Codex, validate, test, correct errors, review with AI, package evidence, and wait for human approval.

## Create A New Phase

1. Create a prompt in `docs/codex-prompts/`.
2. Add required files and tests to `scripts/phase_validator.py`.
3. Implement the phase in a feature branch.
4. Add or update tests.
5. Run:

```text
python ai-factory/run_ai_factory.py --phase <phase>
```

## How Codex Works In This Flow

Codex remains the implementation agent. It writes code, documentation, tests, and reports. The factory runner does not replace Codex; it checks and packages the work Codex produced.

## How Tests Run

The runner executes:

```text
python scripts/phase_validator.py --phase <phase>
pytest tests/test_phase13_8_ai_factory.py
```

For future phases, the phase-specific test command can be updated in the runner or wrapped by n8n.

## How Ollama Reviews

The runner calls:

```text
python ai-review/run_phase_review.py --phase <phase> --skip-migration
```

That existing review engine gathers evidence, validates rules, executes its configured tests, calls the Ollama reviewer, and generates `docs/reviews/PHASE_AI_REVIEW_REPORT.md`.

## How n8n Triggers Workflow

n8n can trigger the same workflow externally through the Phase 13.7 controller:

```text
python scripts/n8n_phase_trigger.py --phase <phase>
```

If `N8N_WEBHOOK_URL` is configured, the trigger can send an event to n8n. If not, it runs in local controller mode.

## Safety Rules

- No production deployment
- No automatic merge
- No hidden test failures
- No approval bypass
- Human review remains mandatory
