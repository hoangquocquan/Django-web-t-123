# Legacy AI Settings

The old custom backend used these environment variables before AI was moved to the Django AI Platform:

- `MEC_OLLAMA_URL`
- `MEC_OLLAMA_MODEL`
- `MEC_OLLAMA_TIMEOUT_SECONDS`

These settings are intentionally removed from `backend/config/settings.py`.
Use the Django AI Platform configuration for active Ollama and RAG features.
