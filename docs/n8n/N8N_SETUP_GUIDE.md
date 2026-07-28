# n8n Setup Guide

## Local Installation

Install n8n locally when you want to test orchestration without production
deployment.

Example:

```powershell
npx n8n
```

Open:

```text
http://localhost:5678
```

## Docker Installation

Example local-only container:

```powershell
docker run --rm -it -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n
```

## Environment Variables

Use environment variables. Do not commit real values.

```text
N8N_WEBHOOK_URL=
N8N_API_KEY=
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

## Security Configuration

- Keep real secrets outside Git.
- Limit webhook access to trusted systems.
- Require human approval before staging or production actions.
- Do not add production deployment nodes to the Phase 13.3 workflow.

## Import Workflow

Import this file into n8n:

```text
docs/n8n/n8n_cicd_pipeline_workflow.json
```

The workflow is inactive by default. Review every command before activation.

## Local Dry Run

If n8n is not running, generate local orchestration evidence:

```powershell
python scripts/n8n_phase_trigger.py
python scripts/n8n_ollama_review.py
```
