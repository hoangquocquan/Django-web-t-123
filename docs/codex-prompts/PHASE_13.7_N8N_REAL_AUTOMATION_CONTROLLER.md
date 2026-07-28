# TASK: Phase 13.7 - n8n Real Automation Controller

Project:

mecprecision-vietnam

## Objective

Create real n8n automation controller.

Goal:

n8n becomes the orchestrator connecting:

- Testing
- Error Correction
- Ollama Review
- Reporting

## Important Rules

DO NOT:

- auto deploy production
- auto merge code
- bypass human approval
- hide failed tests

n8n only:

- trigger workflows
- execute automation
- collect results
- notify status

## Target Workflow

Trigger

↓

n8n Controller

↓

Run Phase Validation

↓

Run Tests

↓

PASS or FAIL

PASS:

- Ollama Review
- Review Report

FAIL:

- Error Analysis
- Auto Fix Task
- Codex Fix
- Test Again

## Git Requirements

Branch:

feature/phase-13.7-n8n-real-automation-controller

Commit:

feat: add n8n real automation controller

Tag:

phase-13.7-n8n-controller-ready

## Final Status

N8N_AUTOMATION_CONTROLLER_COMPLETE

READY_FOR_AI_SOFTWARE_FACTORY
