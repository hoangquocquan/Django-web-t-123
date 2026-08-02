# PROD-01 Business UI And UAT Completion

## Objective

Complete role-based Business UI workflows for Sales and CRM while preserving
human quotation approval and the existing Django ownership boundaries.

## Scope

- Map every Business UI page to its owning module permission.
- Add Sales lead, assignment, opportunity, follow-up, quotation, approval, and
  handoff actions.
- Add CRM interaction, note, task, owner, due date, and timeline actions.
- Render AI Sales and document results as structured fields rather than raw
  Python dictionaries.
- Validate role access, CSRF, server-side input rules, and browser behavior.

## Safety Gates

```json
{
  "human_approval_required": true,
  "auto_merge": false,
  "auto_deploy": false,
  "approval_bypass_detected": false
}
```

AI may draft recommendations, but it cannot approve quotations, perform the
human handoff, merge code, or deploy this phase.

## Acceptance Criteria

- Correct roles can read and write only their modules.
- Missing permissions return HTTP 403.
- Quotation approval requires `sales:approve` and records an audit activity.
- Handoff cannot run before approval.
- Browser writes enforce CSRF and server-side validation.
- Full workflow and real Chrome smoke tests pass.
- Mandatory local Ollama review is schema-valid with no Critical or High finding.

## Rollback

Revert the dedicated PROD-01 commit. The migration removes only the new
`sales:approve` permission definition; no legacy table or legacy code is changed.
