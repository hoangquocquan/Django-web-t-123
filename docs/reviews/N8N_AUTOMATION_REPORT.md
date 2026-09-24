# n8n Automation Report

## Status

PASS

## Implemented

- Local n8n workflow definition: `n8n/workflows/business_wave2_automation.json`.
- Local security config: `n8n/config/business_wave2_local.yml`.
- Local automation helper: `scripts/n8n_business_wave2.py`.

## Workflows

- Website Lead -> Django CRM -> AI Lead Analysis -> Sales Notification.
- New Document -> OCR/Text Extraction -> Knowledge Update.
- Sales Follow-up -> Reminder -> Notification.

## Security

- HMAC SHA-256 webhook validation.
- Workflows inactive by default.
- Local only.
- No production deployment.
- No external email.
- Human approval required.

## Tests

```powershell
pytest tests\test_n8n_automation.py -q
```

Result: PASS.

