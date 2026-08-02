# Controlled Rollback Plan

1. Human incident owner declares rollback or forward-fix decision.
2. Stop new writes through the approved maintenance mechanism.
3. Restore the previously approved immutable application image and configuration.
4. Prefer forward-fix migrations; reverse only migrations explicitly proven reversible.
5. Restore PostgreSQL/media/n8n only from a verified pre-deployment backup when
   the human database owner confirms data-loss impact.
6. Reconnect the approved local Ollama model endpoint and Redis configuration.
7. Run health, authentication, CRM, Sales, Knowledge and automation smoke tests.
8. Monitor errors/latency and preserve incident evidence.

No rollback was executed against production in PROD-07.
