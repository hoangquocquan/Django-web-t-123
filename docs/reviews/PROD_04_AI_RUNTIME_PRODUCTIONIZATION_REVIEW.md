# PROD-04 AI Runtime Productionization Review

## Phase

- Date: 2026-08-02
- Branch: `codex/production-readiness-full`
- Baseline: `c11660a190f02f961d6906290c44284c25d1bb19`
- Phase commit: `38ebfe3fcd7b03652764bee311fc5c99fb631270`
- Decision: `PASS_WITH_WARNINGS`
- Next-phase eligibility: `READY_FOR_NEXT_PHASE`

## Objective And Scope

PROD-04 productionizes local Ollama inference, distributed Redis controls, RAG
health/quality validation, and a live PostgreSQL-backed n8n orchestration gate.
AI Sales remains draft-only and Agent tools remain explicit, audited, bounded,
permission-protected, and read-only.

## Architecture And Data Impact

- Generation, embedding, and review models use purpose-specific server allowlists;
  request serializers do not expose model selection.
- Ollama generation obtains a leased Redis capacity slot shared across workers.
  Redis also remains the atomic distributed request-rate backend in production.
- RAG health reports endpoint/model state, document/chunk/vector counts, coverage,
  stale document IDs, and the safe reindex command without returning source text.
- The bilingual benchmark uses a real authorized user so document-level filtering
  is applied. Two anonymous local benchmark documents produced real Ollama vectors.
- No schema migration was created. Local PostgreSQL stores benchmark/index data and
  n8n runtime persistence; these runtime rows are not committed.

## n8n Safety

- n8n `2.21.7` runs healthy with PostgreSQL persistence and encrypted local state.
- The webhook validates HMAC-SHA256, correlation ID, and all four safety gates.
- Bounded Django health retries are limited to three attempts.
- A safe request returned `200` with `phase_advanced=false`; invalid signature and
  valid-signature `auto_deploy=true` requests both returned `401`.
- The error workflow records a local fail-closed result and has no external action.

## Validation Results

- Compile, Django check, migration drift, and PostgreSQL migration check: PASS.
- Focused PROD-04/vector tests: 22 passed.
- Root full regression: 490 passed, 0 failed.
- Migration regression: 238 passed, 0 failed.
- Changed-scope Ruff/format, mypy, and AI-scope Bandit: PASS.
- Production/development dependency audits: no known vulnerabilities.
- Docker production-like stack: web, PostgreSQL, Redis, and n8n healthy.
- Real Redis shared sequence: `1, 2, 3`; real bilingual RAG confidence:
  Vietnamese `0.8755`, English `0.8916`.
- Real RAG generation cited both retrieved source titles with no hallucination warning.

## Mandatory Ollama Review

- Model: `llama3`
- Decision: PASS
- Schema valid: true
- Fallback used: false
- Critical/High/Medium findings: 0/0/0
- Final attempts: 1
- Gate state: `WAITING_HUMAN_APPROVAL`

An earlier review used prohibited merge authorization wording. The deterministic
gate was hardened with an additional regression test, evidence was regenerated,
and the final real Ollama response contains no merge or deployment authorization.

## Tools Not Run

- Docker Scout was attempted but requires Docker ID authentication.
- Full-repository Ruff/format and default mypy retain pre-existing legacy debt;
  changed-scope checks pass and no unrelated bulk refactor was performed.
- Browser E2E was not rerun because PROD-04 changes runtime APIs/orchestration,
  not visual UI. Live API/RAG/n8n integration checks passed.

## Known Limitations

- JSON-backed vectors are suitable for the current small corpus, not high-scale
  semantic search; pgvector remains the recommended scale-up path.
- Production TLS, external n8n worker topology, and real secret rotation require
  infrastructure-specific human configuration.

## Rollback

Revert the dedicated phase commit, restore the previous Compose definition, and
stop only the project-owned n8n service if required. Do not remove PostgreSQL or
n8n volumes without a separately approved backup/retention decision.

## Final Decision

`PASS_WITH_WARNINGS`. PROD-05 may start. This review does not authorize merge,
push, tag, staging deployment, or production deployment. Human approval remains
mandatory for every protected action.
