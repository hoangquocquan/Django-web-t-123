# Pipeline Stages

## 1. Source Checkout

Checkout the exact commit being reviewed or deployed.

Required:

- Commit hash recorded.
- Branch recorded.
- Tag recorded when release or phase review requires it.

## 2. Dependency Install

Install Python, Django, test, and tooling dependencies.

Required:

- Use locked dependencies when available.
- Do not install production secrets.

## 3. Lint

Run style and static checks when configured.

Future tools:

- Ruff
- Black check mode
- mypy

## 4. Unit Test

Run focused unit tests and module tests.

Baseline command:

```powershell
pytest
```

## 5. Security Scan

Run security and dependency checks.

Future tools:

- pip-audit
- Safety
- Bandit
- secret scanner

## 6. Build

Create immutable build artifacts.

Examples:

- Docker image.
- Static frontend package.
- Documentation package.

## 7. Deploy

Deploy only to the approved environment.

Rules:

- Development/testing may be automated.
- Staging needs manual gate.
- Production needs manual approval and rollback readiness.

## 8. Health Check

Run application, API, database, and dependency checks after deployment.

Existing foundation:

```powershell
python scripts/phase12_3_health_check.py
```

## 9. AI Review

Run local AI-assisted review through Ollama after validation artifacts exist.

Existing foundation:

```powershell
python scripts/phase_validator.py
python scripts/ollama_phase_reviewer.py
```

AI review is advisory only and cannot approve production.

