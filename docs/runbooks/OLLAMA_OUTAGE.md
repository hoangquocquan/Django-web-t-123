# Ollama Outage

1. Confirm Ollama endpoint reachability and configured model availability.
2. Keep RAG source retrieval available, but return a clear local-model-unavailable response; fallback cannot claim AI success.
3. Check host capacity and model process logs without sending prompts externally.
4. Restore the approved local model and rerun health plus a source-grounded smoke query.
5. No external AI provider may be enabled as an emergency bypass.
