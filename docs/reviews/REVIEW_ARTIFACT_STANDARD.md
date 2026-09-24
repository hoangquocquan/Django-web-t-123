# Review Artifact Standard

Every phase must generate:

1. `PHASE_X_REVIEW_SUMMARY.md`
2. `PHASE_X_CHANGESET.patch`

For minor phases, use the full minor version:

```text
PHASE_3.1_REVIEW_SUMMARY.md
PHASE_3.1_CHANGESET.patch
```

## Review Package Must Include

- objective
- base commit
- final commit
- changed files
- architecture decisions
- database impact
- API impact
- security review
- tests
- risks
- next step

## Git Source Of Truth

Git history is the source of truth.

Every review package must be traceable with:

```text
git diff BASE_COMMIT FINAL_COMMIT
git log
git show
```

## Required Patch Command

```text
git diff BASE_COMMIT FINAL_COMMIT > docs/reviews/PHASE_X_CHANGESET.patch
```

## Required Review Status

Every review summary must end with one of:

```text
WAITING FOR ARCHITECT REVIEW
APPROVED
NEEDS CHANGES
```
