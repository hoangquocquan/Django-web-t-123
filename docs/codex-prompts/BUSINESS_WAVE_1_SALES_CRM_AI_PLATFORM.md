# AI BUSINESS WAVE 1
# SALES CRM AI PLATFORM

## Objective

Build a Sales + CRM + AI Sales Assistant platform on top of the existing Django system.

## Scope

- Sales lead, opportunity, quotation, follow-up, activity, and dashboard APIs.
- CRM customer profile, timeline, interaction, note, task, and segmentation APIs.
- AI Sales Assistant for lead analysis, customer summary, email draft, and sales recommendations.
- RAG connection to local knowledge data only.

## Safety Rules

- Do not use external AI APIs.
- Do not bypass Django permissions.
- Do not allow AI to perform autonomous business actions.
- Do not rewrite product, customer, or order core.
- Human approval is always required for AI suggestions.

## API Requirements

- `/api/v1/sales/leads/`
- `/api/v1/sales/opportunities/`
- `/api/v1/sales/quotations/`
- `/api/v1/crm/customers/`
- `/api/v1/ai/sales-assistant/`

## Testing Requirements

- `python manage.py check`
- `pytest tests/test_sales_crm_ai.py`
- `pytest`

## Review Requirements

- `ai-factory/evidence/business_wave_1.json`
- `docs/reviews/BUSINESS_WAVE_1_SALES_CRM_AI_REVIEW.md`
- `docs/reviews/BUSINESS_WAVE_1_SALES_CRM_AI_FINAL_REPORT.md`

## Git Requirements

- Branch: `feature/sales-platform`
- Commit: `feat: build sales crm ai platform`
- Tag: `business-wave-1-complete`

## Final Status

`MEC_SALES_CRM_AI_PLATFORM_COMPLETE`
