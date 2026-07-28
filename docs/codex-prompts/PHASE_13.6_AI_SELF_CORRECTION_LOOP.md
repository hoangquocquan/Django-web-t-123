# TASK: Phase 13.6 - AI Self Correction Loop

Project:

mecprecision-vietnam

## Objective

Create an AI-assisted error correction loop.

Goal:

When automated tests fail:

1. Capture error
2. Analyze failure
3. Generate fix instruction
4. Let Codex apply correction
5. Re-run tests
6. Produce final result

## Important Rules

DO NOT:

- allow AI to modify production automatically
- skip failed tests
- hide errors
- create fake PASS result

AI can:

- analyze errors
- suggest fixes
- create fix tasks

Human approval required before final merge.

## Target Flow

Test Execution

↓

Failure Detector

↓

Error Collector

↓

Ollama Error Analysis

↓

Codex Fix Task Generator

↓

Codex Correction

↓

Test Retry

↓

Final Report

## Git Requirements

Branch:

feature/phase-13.6-ai-self-correction-loop

Commit:

feat: add ai self correction loop

Tag:

phase-13.6-self-correction-ready

## Final Status

AI_SELF_CORRECTION_LOOP_COMPLETE

READY_FOR_N8N_AUTOMATION
