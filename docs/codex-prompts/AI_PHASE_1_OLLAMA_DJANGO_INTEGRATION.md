# AI Phase 1 - Ollama Django Integration

## Objective

Integrate local Ollama LLM into Django and create the reusable AI foundation
layer.

## Scope

- Local Ollama client.
- Prompt manager.
- Authenticated AI chat API.
- Local-only configuration.
- Documentation, tests, evidence, and review package.

## DO NOT

- Do not use paid AI APIs.
- Do not expose Ollama publicly.
- Do not store sensitive prompt content.
- Do not modify business modules.
- Do not create AI agents.

## Implementation Tasks

1. Add `apps.ai`.
2. Add `OllamaClient`.
3. Add `PromptManager`.
4. Add `POST /api/v1/ai/chat/`.
5. Add Ollama environment settings.
6. Add tests.
7. Add documentation and evidence.

## Testing Requirements

- `python django_backend/manage.py check`
- `pytest tests/test_ai_ollama.py`
- `pytest`
- `python ai-factory/run_ai_factory.py --phase ai-1`

## Git Requirements

- Branch: `feature/ai-phase-1-ollama-integration`
- Commit: `feat: integrate ollama ai foundation`
- Tag: `ai-phase-1-complete`

## Expected Output

Final status: `AI_OLLAMA_FOUNDATION_COMPLETE`.

