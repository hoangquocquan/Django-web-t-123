# AI-03 Grounded Sales AI Synthesis

## Objective

Use local Ollama for sales explanations and email drafts while deterministic Django code remains the only owner of lead scores and business facts.

## Dependencies

- AI-01 vector retrieval must provide ranked, identifiable knowledge sources.
- AI-02 governance must reject unsafe requests before synthesis.
- Local Ollama generation model is configured by `OLLAMA_MODEL`.

## Scope

- Structured Facts, Ollama Synthesis, Validation and deterministic Fallback layers.
- Strict JSON output with source ID validation and mandatory human approval.
- Structured Business UI cards instead of a raw Python dictionary.
- Unit, integration, offline and real-data validation.

## Safety Rules

- The model cannot calculate, return or mutate the lead score.
- The model cannot send email, update CRM, approve quotations, discount, create orders or move pipeline stages.
- Unknown source IDs and contradictory pipeline claims are rejected.
- Failure is reported as `generation_mode=fallback`; it is never presented as Ollama success.
- Prompt content and unnecessary PII are not logged.

## Acceptance Criteria

- Valid local Ollama JSON passes schema and grounding validation.
- Invalid JSON, missing fields, unknown sources and dangerous outputs fail safely.
- Lead score is unchanged before and after synthesis.
- Email output remains draft-only and requires human approval.
- Focused and regression tests pass.
- Independent local Ollama review has no Critical or High finding.

## Rollback

Revert the AI-03 commits. Existing deterministic Sales/CRM models and APIs require no database rollback because this phase creates no migration.

## Expected Commit

`feat(ai-sales): add grounded ollama sales synthesis`
