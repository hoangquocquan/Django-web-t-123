# AI Service Architecture

## Architecture

```mermaid
flowchart TD
    Browser["Authenticated client"]
    Api["Django API /api/v1/ai/chat/"]
    Permission["FoundationAuthService + FoundationPermissionService"]
    Prompt["PromptManager"]
    Client["OllamaClient"]
    Ollama["Local Ollama API"]
    Model["Local LLM model"]

    Browser --> Api
    Api --> Permission
    Api --> Prompt
    Prompt --> Client
    Client --> Ollama
    Ollama --> Model
```

## Components

`apps.ai.views`

Receives HTTP requests, validates JSON input, checks Bearer token access, and
returns the standard project JSON envelope.

`PromptManager`

Normalizes the user message, enforces the message length limit, and builds the
system prompt. It does not store prompts or responses.

`OllamaClient`

Calls local Ollama endpoints:

- `GET /api/tags`
- `POST /api/generate`

It includes timeout handling, retry handling, invalid JSON protection, and safe
logging that avoids prompt content.

## Security

- Ollama remains local-only.
- No external AI API is called.
- Authentication is required.
- AI write permission is required.
- Prompt content is not persisted in Phase 1.

## Legacy Cleanup

The old custom backend AI service has been archived and removed from runtime.
Active AI calls must go through Django AI Platform endpoints only:

- `/api/v1/ai/chat/`
- `/api/v1/knowledge/chat/`
- `/api/v1/ai/sales-assistant/`

Archive references:

- `docs/ai/LEGACY_AI_INVENTORY.md`
- `docs/ai/LEGACY_AI_ARCHIVE.md`
