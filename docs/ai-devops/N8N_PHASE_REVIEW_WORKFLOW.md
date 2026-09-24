# n8n Phase Review Workflow

## Purpose

This workflow describes how n8n can automate repetitive migration review steps
while keeping approval in human hands.

## Trigger

Supported triggers:

- Manual trigger by operator.
- Git push trigger from a controlled repository event.

## Workflow Steps

1. Collect phase information.
2. Run `python scripts/phase_validator.py`.
3. Run phase-specific tests.
4. Run regression tests.
5. Send phase prompt, changed files, test result, and validation JSON to Ollama.
6. Generate `docs/ai-devops/AI_PHASE_REVIEW_REPORT.md`.
7. Notify the developer and architecture reviewer.

## Example Commands

```powershell
python scripts/phase_validator.py
python scripts/ollama_phase_reviewer.py
pytest tests/test_phase12_4_ai_devops.py
pytest
```

## Ollama Request

Default endpoint:

```text
http://localhost:11434/api/generate
```

Default model:

```text
llama3.1
```

The model can be changed with:

```powershell
$env:OLLAMA_MODEL="llama3.1"
```

## Human Review Boundary

n8n may notify reviewers and generate reports. It must not merge branches,
deploy production, approve shutdown, or mark production as accepted.

