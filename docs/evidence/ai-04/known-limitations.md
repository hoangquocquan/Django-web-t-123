# Known Limitations

- Per-tool timeout stops waiting and records failure, but Python cannot forcibly terminate a thread already inside third-party code. Only audited read-only tools are therefore allowed.
- Planner fallback is deterministic and labelled; it is used in tests and when local Ollama is disabled or unavailable.
- Agent answers are deterministic compositions of tool outputs. Free-form LLM synthesis is intentionally excluded from this phase.
- Audit records are operational writes; business models remain read-only to the agent.
