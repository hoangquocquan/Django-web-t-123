# AI CI/CD Integration

## Purpose

This document mirrors the CI/CD AI integration boundary for tools that read
from `docs/ai-devops`. The canonical design lives in:

```text
docs/cicd/AI_CICD_INTEGRATION.md
```

## AI Role

AI can summarize test results, review missing artifacts, highlight risks, and
prepare a concise advisory decision.

Possible advisory decisions:

- `PASS`
- `PASS_WITH_WARNING`
- `BLOCKED`

## Human Boundary

AI cannot:

- deploy production automatically
- approve production
- create real CI secrets
- bypass failed tests

AI can recommend. Humans decide.

## Phase 13.2 Use

The automated test pipeline writes test evidence to:

```text
docs/cicd/test_pipeline_result.json
```

The AI advisory review writes to:

```text
docs/ai-devops/TEST_PIPELINE_AI_REVIEW.md
```
