# AI Core Upgrade - Ollama Real Inference

## Objective

Upgrade the Django AI platform from source fallback mode to real local Ollama inference while preserving RAG grounding.

## Scope

- Ollama health management.
- Local model configuration.
- RAG retrieval, context ranking, prompt template, Ollama generation, and source citation.
- Response quality metadata.
- AI request monitoring log.
- AI Sales Assistant quality metadata.

## DO NOT

- Do not use external AI APIs.
- Do not use OpenAI API.
- Do not expose Ollama publicly.
- Do not remove RAG grounding.
- Do not allow autonomous business actions.

## Testing

- `python django_backend/manage.py check`
- `pytest tests/test_ollama_real_inference.py`
- `pytest`

## Expected Output

- `/api/v1/ai/health/` reports local Ollama status.
- Knowledge assistant calls Ollama when available.
- Knowledge assistant returns source-based fallback when Ollama is unavailable.
- AI request monitoring stores safe metadata only.
- AI Sales Assistant includes confidence and source relevance without executing business actions.
