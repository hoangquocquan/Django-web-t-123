# AI-06 Final Integration, Validation and Handover

## Objective

Validate the cumulative AI hardening implementation from AI-01 through AI-05
against the current repository, run the mandatory local Ollama review, and
prepare an auditable handover that stops at human approval.

## Baseline Commit

`e10b456d21e1c190b2944fbe79befb88d81d4763`

This is the integration commit immediately before the AI-01 implementation.

## Commit Map

| Phase | Implementation commit | Integration or V2 commit |
| --- | --- | --- |
| AI-01 | `a2751c3e33e0c55cec50045fe6d131701a7a1d15` | `3bbd6b6f609a984b062f7059104c07d9b8edd2f1` |
| AI-02 | `5e10202a70164f410acc9e5bb273d1d1dc3661c7` | `db7c934369a7db97997c27ac87c0e8691314d582` |
| AI-03 | `03b17e404374de75afa569d69e3a18fd38ca03c0` | `d06f2f382bc8c26580d775b157ae10d4a70b53cb` |
| AI-04 | `a5175d9f9c03daf9e6cf1e06ab0c64329d9802c2` | `92174f2d2cac9897e61bd7f13ebd903a8779fd64` |
| AI-05 | `fbf594f4f9a017a46b6d7049fe258e0204af9fc2` | `81232332776fd30f22d607b61ac8aec9706d7f38` |

## Scope

- Verify source, migrations, tests, evidence, reviews, and commits for AI-01
  through AI-05.
- Validate compilation, Django configuration, migration drift, focused tests,
  regression tests, static analysis, dependency configuration, and runtime
  integration.
- Review the cumulative Git change from the baseline through the current
  source with the mandatory local Ollama reviewer.
- Produce AI-06 evidence, final review, result, handover, status, known issues,
  approval queue, and a dedicated local commit.

## Out Of Scope

- Merging into `main` or another shared branch.
- Pushing to a remote.
- Creating a release tag.
- Staging or production deployment.
- Automatic merge, automatic deployment, or AI self-approval.
- Unrelated business behavior or broad inherited-debt refactoring.

## Dependency Graph

```text
AI-01 Vector Retrieval
  -> AI-03 Grounded Sales Synthesis

AI-02 Governance V2
  -> AI-03 Grounded Sales Synthesis
  -> AI-04 Safe Agent Controller

AI-01 + AI-02 + AI-03 + AI-04
  -> AI-05 Mandatory Review Gate

AI-01 .. AI-05
  -> AI-06 Final Integration and Handover
```

## Allowed Paths

- `docs/codex-prompts/AI_06_FINAL_INTEGRATION.md`
- `docs/evidence/ai-06/`
- `docs/reviews/AI_SYSTEM_HARDENING_V2_*`
- Integration source and tests only when a concrete validation blocker requires
  a narrowly scoped fix.

Runtime databases, `.env`, ZIP files, caches, logs containing PII, backups, and
secrets are forbidden from the commit.

## Validation Matrix

- Compile Python source.
- Django system check.
- Migration drift check.
- Focused AI-01, AI-02, AI-03, AI-04, and AI-05 tests.
- Full regression.
- Ruff and Ruff format when installed.
- Mypy for changed source paths.
- Bandit security scan with inherited findings identified separately.
- Pip dependency audit when installed.
- Docker Compose configuration validation when Docker is available.
- Ollama, RAG, governance, Sales AI, Agent, AI Factory, and n8n integration
  validation.
- Mandatory local Ollama review over cumulative Git evidence.

## Security Gates

```json
{
  "human_approval_required": true,
  "auto_merge": false,
  "auto_deploy": false,
  "approval_bypass_detected": false
}
```

Fallback cannot grant PASS. Invalid review output, missing evidence, failed
required tests, or any new Critical/High finding blocks the phase.

## Acceptance Criteria

- AI-01 through AI-05 implementation is complete in actual source.
- AI-05 V2 dedicated commit exists.
- Required deterministic validation passes.
- Real local Ollama review is schema-valid PASS with no Critical/High finding.
- Evidence and handover artifacts are complete.
- A dedicated AI-06 local commit exists.
- Final workflow state is `WAITING_FOR_HUMAN_APPROVAL`.

## Rollback Plan

Revert only the dedicated AI-06 documentation/evidence commit. If a separate
integration-code fix becomes necessary, revert that code commit first. Never
reset, clean, or discard unrelated user files.

## Commit Policy

Use a separate code commit only for a required integration fix. Finish with:

`docs(ai): hoàn tất tích hợp và bàn giao AI hardening v2`

Do not merge, push, tag, or deploy.
