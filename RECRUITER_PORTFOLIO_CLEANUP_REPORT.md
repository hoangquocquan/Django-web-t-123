# Recruiter Portfolio Cleanup Report

## 1. Branch

`chore/recruiter-ready-portfolio`

## 2. Moved files

Root-level internal handoff, audit, review, readiness, remediation, and development-history Markdown files were moved to `docs/internal/`. Existing structured technical documentation was preserved.

## 3. Created or updated files

- `README.md` — English portfolio overview
- `README_JA.md` — Japanese overview
- `docs/architecture/ARCHITECTURE.md` — application and AWS-oriented diagrams
- `docs/images/README.md` — screenshot checklist and placeholders
- This report

## 4. README changes

The README now presents the project, stack, business flow, personal role, AI-tool disclosure, local entry points, security expectations, and project status without claiming unverified production deployment.

## 5. Architecture documentation

Mermaid diagrams cover the React → Django → PostgreSQL/RAG → AI Sales Assistant → RFQ → n8n → LINE flow and the AWS-oriented Internet → ALB → ECS → RDS architecture, with S3, ECR, CloudWatch, Secrets Manager, and GitHub Actions.

## 6. Screenshots still needed

Add sanitized real screenshots at `docs/images/product-page.png`, `ai-sales-chatbot.png`, `rfq-workflow.png`, and `admin-operations.png`. No fake images were added.

## 7. GitHub About and Topics

Suggested About: `AI-powered automotive parts sales platform built with Django, React, PostgreSQL, RAG, n8n and AWS.`

Suggested topics: `django`, `react`, `postgresql`, `rag`, `ai`, `llm`, `n8n`, `aws`, `docker`, `rest-api`, `github-actions`, `automotive`, `portfolio`, `full-stack`, `ai-assistant`.

The configured remote currently points to `https://github.com/hoangquocquan/Django-web-t-123.git`, not `hoangquocquan/Django_web_auto`; About/topics were not changed automatically.

## 8. Validation results

- README relative links: reviewed; referenced files exist.
- Mermaid: diagrams use standard `flowchart LR` syntax and were reviewed statically.
- Migration check: `python manage.py makemigrations --check --dry-run` passed with no changes.
- Frontend tests: passed, 167 tests.
- Frontend production build: passed with Vite.
- Django system check ran successfully, but the full test command is blocked by pre-existing test imports such as `ModuleNotFoundError: No module named 'scripts'` from `django_backend/tests/test_phase10_*` and `test_phase11_*`.
- Secret-pattern review: no credentials were added; one existing documentation example contains the placeholder `N8N_API_KEY=` and should remain unfilled.
- Final `git status` and changed-file review remain to be performed immediately before commit.

## 9. Warnings

- Pre-existing uncommitted application changes were preserved.
- AWS content is staging/target architecture unless deployment evidence says otherwise.
- Real screenshots are still required.

## 10. Recruiter readiness

Documentation is recruiter-oriented after validation passes. Before sending, add screenshots, verify the intended GitHub remote, review the final diff, and confirm no credentials or private operational data are tracked.
