# Business Wave 2 n8n Automation

This package defines a local-only automation platform for learning and demo use.

## Workflows

- Website Lead -> Django CRM -> AI Lead Analysis -> Sales Notification
- New Document -> OCR/Text Extraction -> Knowledge Update
- Sales Follow-up -> Reminder -> Notification

## Security

- Webhook payloads are validated with HMAC SHA-256.
- Workflows are inactive by default.
- No production deployment is included.
- No external AI API is used.
- Human approval remains required before customer-facing actions.

## Local Test

Run:

```powershell
python scripts\n8n_business_wave2.py
```

Output:

```text
n8n/results/business_wave2_execution.json
```

