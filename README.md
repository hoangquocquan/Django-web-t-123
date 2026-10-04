# AI-Powered Automotive Parts Sales Platform

[English](README.md) | [日本語](README_JA.md)

An engineering portfolio project for automotive parts sales, combining a Django backend, React frontend, retrieval-augmented generation (RAG), and workflow automation.

## Project

The platform supports product discovery, AI-assisted sales conversations, and request-for-quotation (RFQ) workflows. It is a personal engineering project and learning/staging environment; AWS-related material describes staging or target architecture unless explicitly stated otherwise.

## Technology stack

- Django and Django REST API
- React and Vite
- PostgreSQL
- Docker and Docker Compose
- RAG and AI Sales Assistant
- n8n and LINE workflow automation
- GitHub Actions and AWS staging/target architecture

## Business flow

```text
Customer -> React Frontend -> Django REST API -> PostgreSQL / RAG
         -> AI Sales Assistant -> RFQ -> n8n -> LINE
```

## My role

This personal engineering project covers Django backend and REST/API design, PostgreSQL data modeling and migrations, frontend/backend integration, RAG and AI Sales Assistant flows, RFQ/CRM workflows, n8n/LINE automation, Docker, tests, CI, debugging, review, verification, and AWS staging architecture.

AI coding tools were used as implementation and review aids. The code was still checked through tests, API verification, migration checks, frontend builds, and CI-oriented validation.

## Repository structure

```text
django_backend/          Django backend and API
figma_make_frontend/     React/Vite frontend
docs/architecture/       System and AWS-oriented architecture
docs/images/             Real portfolio screenshots and capture notes
docs/internal/           Internal handoff, audit, and development history
.github/workflows/       CI workflows
```

See [the architecture documentation](docs/architecture/ARCHITECTURE.md).

## Local development

```powershell
Set-Location django_backend
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

```powershell
Set-Location figma_make_frontend
pnpm install --frozen-lockfile
pnpm dev
```

Do not commit `.env` files, credentials, tokens, API keys, AWS credentials, or LINE credentials.

## Screenshots

These screenshots were captured from the running local application with fictional demo data. No artificial screenshots are included.

### Product page

![Product page](docs/images/product-page.png)

### AI Sales Assistant

![AI Sales Assistant](docs/images/ai-sales-chatbot.png)

### RFQ workflow

![RFQ workflow](docs/images/rfq-workflow.png)

### Admin operations

![Admin operations](docs/images/admin-operations.png)

Capture and sanitization notes are documented in [docs/images/README.md](docs/images/README.md).

## Project status

Portfolio cleanup and validation details are available in the [internal portfolio report](docs/internal/RECRUITER_PORTFOLIO_CLEANUP_REPORT.md).
