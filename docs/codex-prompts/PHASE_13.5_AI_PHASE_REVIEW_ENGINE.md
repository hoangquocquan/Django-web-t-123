# TASK: Phase 13.5 - AI Phase Review Engine

Project:

mecprecision-vietnam

## Objective

Create a reusable system that automatically reviews any development Phase.

The system must:

1. Collect Phase evidence
2. Validate requirements
3. Run tests
4. Send evidence to Ollama
5. Generate final review report

## Important Rules

AI is only reviewer.

AI must not:

- approve production deployment
- modify code automatically
- skip failed tests

Human approval remains required.

## Target Architecture

Phase Task

↓

Evidence Collector

↓

Rule Validator

↓

Test Executor

↓

Ollama

↓

AI Phase Review Report

## Git Requirements

Branch:

feature/phase-13.5-ai-phase-review-engine

Commit:

feat: create ai phase review engine

Tag:

phase-13.5-ai-review-ready

## Final Status

AI_PHASE_REVIEW_ENGINE_COMPLETE

READY_FOR_N8N_AUTOMATION
