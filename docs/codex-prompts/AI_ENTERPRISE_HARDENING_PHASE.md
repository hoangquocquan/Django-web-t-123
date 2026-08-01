# AI Enterprise Hardening Phase

## Objective

Upgrade the Django AI backend foundation toward enterprise readiness.

## Scope

- Add centralized AI governance checks.
- Add prompt safety policy.
- Add per-user AI rate limiting.
- Add governance audit events.
- Apply governance to AI chat, Knowledge search/chat, Agent run, and AI Sales Assistant.
- Add automated tests.
- Run demo against local real demo data.

## DO NOT

- Do not use external AI APIs.
- Do not deploy production.
- Do not allow autonomous business actions.
- Do not remove existing RAG grounding.
- Do not bypass human approval.

## Acceptance Criteria

- Safe AI requests are allowed and audited.
- Unsafe prompt injection / secret requests are blocked.
- Per-user rate limit returns `429`.
- AI Sales Assistant remains advisory only.
- Demo uses existing local database data.
- Tests pass.
- Review report is created.
- Git commit is created.

## Test Commands

```powershell
python django_backend\manage.py check
python django_backend\manage.py makemigrations --check --dry-run
pytest tests\test_ai_enterprise_governance.py
pytest tests\test_ai_ollama.py tests\test_ollama_real_inference.py tests\test_ai_enterprise_governance.py tests\test_ai_document_intelligence.py tests\test_sales_crm_ai.py
pytest
python scripts\run_ai_enterprise_demo.py
```

## Final Status

`AI_ENTERPRISE_HARDENING_COMPLETE`

