# Production Readiness Master

## Objective

Move the MEC Precision Platform from AI hardening handover through production
readiness validation without merging, pushing, tagging, or deploying.

## Execution Policy

- Phases run sequentially from PROD-00 through PROD-07.
- A dependent phase starts only after the previous phase reaches
  `READY_FOR_NEXT_PHASE`.
- Independent work may run in parallel only in isolated worktrees. This run
  uses serialized tasks because settings, migrations, shared fixtures, and
  runtime evidence overlap.
- Each phase requires implementation or verification, tests, evidence, a local
  Ollama review, a review result, and a dedicated commit.
- Correction attempts are limited to three per phase.

## Safety Gates

```json
{
  "human_approval_required": true,
  "auto_merge": false,
  "auto_deploy": false,
  "approval_bypass_detected": false
}
```

No fallback review can produce PASS. No AI action can approve quotations,
send messages, update CRM autonomously, merge code, or deploy a release.

## Phase Order

1. PROD-00 Baseline Verification
2. PROD-01 Business UI and UAT Completion
3. PROD-02 Production Settings and Infrastructure
4. PROD-03 Security and Upload Hardening
5. PROD-04 AI Runtime Productionization
6. PROD-05 Monitoring, Backup and Disaster Recovery
7. PROD-06 Staging UAT and Production Readiness
8. PROD-07 Controlled Deployment Package and Handover

## Stop Rule

A failed required test, invalid or fallback Ollama review, unresolved Critical
or High finding, unsafe staged artifact, unavailable required dependency, or
exhausted correction limit sets `BLOCKED_REQUIRES_HUMAN` and stops dependent
phases.
