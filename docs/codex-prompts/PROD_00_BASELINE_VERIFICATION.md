# PROD-00 Baseline Verification

## Objective

Establish a reproducible production-readiness baseline from the committed
AI-06 handover before changing application behavior.

## Baseline

- Branch source: `codex/ai-06-final-integration`
- Baseline commit: `65b77beefbb80f715baf5d30f2a70c22d7bb5d44`
- Working branch: `codex/production-readiness-full`

## Scope

- Verify AI-01 through AI-06 source and Git history.
- Inspect migrations, tests, dependencies, Docker, PostgreSQL, Redis, Ollama,
  and n8n.
- Detect tracked secrets, runtime databases, backups, caches, logs, and ZIPs.
- Run compile, Django, migration, focused, regression, security, configuration,
  runtime health, and mandatory local Ollama review gates.

## Out Of Scope

- Application feature changes.
- Database schema changes or migrations.
- Removing legacy or user files.
- Merge, push, tag, or deployment.

## Acceptance Criteria

- Baseline and dependency state are truthfully recorded.
- Required deterministic checks pass.
- No unresolved Critical or High finding exists.
- Mandatory local Ollama review returns schema-valid PASS without fallback.
- Warnings have explicit impact and retry guidance.
- Evidence, review, result, and dedicated commit exist.

## Rollback

Revert only the dedicated PROD-00 documentation commit. Do not reset or clean
the worktree and do not remove user ZIP files.
