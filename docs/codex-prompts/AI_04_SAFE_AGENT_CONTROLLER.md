# AI-04 Safe Structured Agent Controller

## Objective

Replace keyword-only simulated execution with a structured local planner, strict tool registry, bounded read-only controller and per-tool security audit.

## Dependencies

- AI-02 governance protects the public agent endpoint.
- AI-03 provides the structured Ollama JSON pattern and explicit fallback semantics.
- Django Foundation remains the authority for user permissions.

## Scope

- Structured plan contract and strict schema validation.
- Tool metadata: schemas, permission, risk, read-only flag, timeout, modules and audit requirement.
- Read-only tools for knowledge, customer, lead, sales pipeline, inventory and system health.
- Lifecycle states, per-tool timeout, total limit, bounded output and audit records.
- Compatibility tools remain read-only and cannot execute arbitrary SQL, shell or files.

## Prohibited Capabilities

Arbitrary shell, arbitrary SQL, business database writes, email sending, quotation approval, deployment and deletion are not present in the registry. Audit writes are the only controller database writes.

## Acceptance Criteria

- Unknown tools, missing permissions, invalid arguments, loops and excessive steps are blocked before execution.
- Shell, SQL-write, email-send, approval, deployment and deletion requests are blocked.
- Timeout and tool exceptions produce explicit failure records, never fabricated data.
- Every executed tool creates a correlation-linked audit with input hash, output summary, latency and policy decision.
- Real Ollama planning and real read-only tools pass on local data.
- Full regression and independent Ollama review pass.

## Rollback

Revert AI-04 commits and reverse migration `ai_agent.0002` only on a non-production database after preserving audit evidence.

## Expected Commit

`feat(ai-agent): add safe structured read-only agent controller`
