# Ollama Model Guide

This project uses Ollama as a local-only AI runtime. The Django AI platform must never send prompts, customer data, quotes, or knowledge documents to an external AI API.

## Local Runtime

Default endpoint:

```text
http://localhost:11434
```

Recommended local commands:

```powershell
ollama serve
ollama pull llama3
ollama run llama3
```

## Environment Variables

`OLLAMA_HOST`
: Local Ollama endpoint. Default: `http://localhost:11434`.

`OLLAMA_MODEL`
: Selected local model. Default: `llama3`.

`OLLAMA_TEMPERATURE`
: Controls how creative the answer is. Lower values are safer for business Q&A. Default: `0.2`.

`OLLAMA_NUM_PREDICT`
: Maximum generated token count. Default: `512`.

`OLLAMA_TIMEOUT_SECONDS`
: Request timeout for local model calls. Default: `30`.

## Health API

Check local AI status:

```http
GET /api/v1/ai/health/
```

Example response:

```json
{
  "status": "ready",
  "available": true,
  "model": "llama3.1",
  "model_available": true
}
```

## RAG Flow

The assistant follows this sequence:

```text
User question
-> Knowledge search
-> Retrieved documents
-> Ranked context
-> Safe prompt template
-> Local Ollama
-> Source-grounded answer
-> Confidence and citation metadata
```

If Ollama is unavailable, the assistant returns a deterministic source-based fallback answer instead of inventing information.

## Monitoring

AI request logs store only safe metadata:

- user email
- question hash
- short question preview
- retrieved document ids and titles
- model name
- response time
- confidence
- warning/status

The log does not store full prompts or hidden system instructions.
