# AI Project 1 - MEC Precision AI Knowledge Assistant

## Objective

Build an internal AI assistant that answers questions from controlled MEC
Precision knowledge sources.

## Scope

- Knowledge source management.
- Document processing pipeline.
- Semantic search with sources and confidence.
- Source-grounded knowledge chat through local Ollama.
- Read-only business context connection.
- Quality control and audit logging.

## DO NOT

- Do not use external AI APIs.
- Do not expose Ollama publicly.
- Do not enable AI write actions.
- Do not bypass Django permissions.
- Do not remove human approval.

## Implementation Tasks

1. Extend `apps.knowledge` document models.
2. Add document category, permission, version, and assistant log models.
3. Add document processing and indexing services.
4. Add knowledge documents API.
5. Add source-grounded search and chat APIs.
6. Add read-only business context connector.
7. Add tests, evidence, and review reports.

## Testing Requirements

- `python django_backend/manage.py check`
- `pytest tests/test_ai_knowledge_assistant.py`
- `pytest`
- `python ai-factory/run_ai_factory.py --project ai-knowledge-assistant`

## Git Requirements

- Branch: `feature/ai-project-1-knowledge-assistant`
- Commit: `feat: build mec knowledge assistant`
- Tag: `ai-project-1-complete`

## Expected Output

Final status: `MEC_AI_KNOWLEDGE_ASSISTANT_COMPLETE`.

