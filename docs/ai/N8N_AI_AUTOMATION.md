# n8n AI Automation

## Goal

n8n is used as a local workflow orchestration layer around Django AI APIs.
AI Wave 1 documents and provides local workflow definitions only. It does not
deploy n8n to production.

## Workflow 1: Contact Classification

Website contact form sends data to Django. n8n can call Django AI endpoints to
classify the contact and prepare a CRM notification.

## Workflow 2: Knowledge Update

When a new document is approved, n8n can trigger RAG ingestion and update the
knowledge index.

## Workflow 3: System Event Analysis

System events can be sent to a local workflow that asks AI to summarize impact
and notify the operator.

## Security

- n8n must run locally or inside a private network.
- Webhooks must be validated.
- Secrets must live in environment variables or n8n credentials.
- No business data is sent to external AI APIs.

## Local Workflow File

`n8n/workflows/ai_contact_classification.json`

