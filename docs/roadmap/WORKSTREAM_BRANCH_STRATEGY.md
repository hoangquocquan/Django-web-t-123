# Workstream Branch Strategy

## Required Branches

| Workstream | Branch |
| --- | --- |
| Frontend ownership | `feature/frontend-migration` |
| Sales platform | `feature/sales-platform` |
| CRM system | `feature/crm-system` |
| AI sales assistant | `feature/ai-sales` |
| AI document intelligence | `feature/ai-document` |
| n8n automation | `feature/n8n-automation` |
| AI Factory V2 | `feature/ai-factory-v2` |

## Rules

- Never mix unrelated workstreams.
- Each workstream needs its own tests and final report.
- Do not merge automatically.
- Human review remains required.
- Do not deploy production from workstream branches.

## Commit Convention

- `docs:` documentation only
- `feat:` new implementation
- `fix:` bug fix
- `test:` test changes
- `chore:` tooling and governance

