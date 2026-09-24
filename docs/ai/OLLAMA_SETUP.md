# Ollama Setup

## Purpose

This project uses Ollama as a local-only LLM runtime. Django talks to Ollama on
the developer machine or private server. No paid AI API and no external AI
service are required for AI Phase 1.

## Installation

Install Ollama from the official Ollama installer, then start the local service.
The default local endpoint is:

`http://localhost:11434`

## Model Selection

Recommended local models:

- Qwen: good general reasoning and multilingual support.
- Llama: good general assistant behavior.
- Mistral: lightweight and fast for smaller machines.

Example local command:

`ollama run llama3`

## Django Configuration

Set these values in `django_backend/.env`:

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT_SECONDS=30
AI_CHAT_MAX_MESSAGE_LENGTH=2000
```

## Resource Requirements

Small models can run on CPU, but responses are slower. Larger models need more
RAM and benefit from GPU acceleration. Keep Ollama private and do not expose the
Ollama port directly to the public internet.
