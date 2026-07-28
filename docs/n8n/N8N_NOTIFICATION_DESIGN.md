# n8n Notification Design

## Purpose

Notifications turn pipeline evidence into clear reviewer actions. They do not
approve deployment and do not execute production changes.

## Success Notification

When required stages pass:

```text
Subject: Phase CI/CD orchestration passed
Status: PASS or PASS_WITH_WARNING
Artifacts:
- docs/n8n/n8n_execution_report.json
- docs/cicd/test_pipeline_result.json
- docs/ai-devops/N8N_AI_REVIEW_REPORT.md
Action: Human review required
```

## Failure Notification

When any required stage fails:

```text
Subject: Phase CI/CD orchestration blocked
Status: BLOCKED
Failed stage: <stage name>
Action: Fix failed checks before review
```

## Security Alert

Security alerts are raised when:

- workflow attempts production deployment
- real secrets appear in workflow JSON
- failed tests are bypassed
- human approval boundary is missing

## Human Approval Request

Approval message must state:

- phase name
- commit hash
- test result
- AI advisory decision
- production safety confirmation

Approval is manual. n8n cannot approve production.
