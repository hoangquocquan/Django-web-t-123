# Branching Strategy

## Branches

| Branch type | Purpose |
| --- | --- |
| `main` | Production-stable branch. Only reviewed and approved releases land here. |
| `develop` | Integration branch for completed and reviewed work. |
| `feature/*` | New features, documentation phases, CI/CD design, or tooling work. |
| `migration/*` | Migration-specific implementation and review phases. |
| `release/*` | Stabilization branch before production release. |
| `hotfix/*` | Urgent production fixes after approval. |

## Merge Requirements

Merging into `develop` requires:

- Passing CI.
- Relevant tests passing.
- Review summary present when phase work is involved.
- Human reviewer approval.

Merging into `main` requires:

- Release branch or hotfix branch.
- Full regression tests.
- Security checks.
- Staging validation.
- Human production approval.

## Review Requirements

Required reviewers:

- Developer reviewer for code quality.
- Architecture reviewer for migration or CI/CD phases.
- Security reviewer when secrets, auth, permissions, or deployment are touched.
- Operations reviewer when production deployment or rollback is touched.

## Protection Rules

Recommended Git protections:

- Block direct push to `main`.
- Block direct push to `develop`.
- Require pull request review.
- Require passing checks.
- Require signed or traceable commits when available.
- Require linear history for release branches if the team adopts it.

## Hotfix Rules

Hotfixes must:

- Start from `main`.
- Include a rollback note.
- Run focused tests and regression tests.
- Merge back into `develop` after production fix is approved.

