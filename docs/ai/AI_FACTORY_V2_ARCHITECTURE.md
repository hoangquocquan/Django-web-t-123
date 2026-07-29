# AI Factory V2 Architecture

## Goal

AI Factory V2 extends the existing review workflow with specialized local AI
roles for safer software delivery.

## Roles

- Requirement Analyzer
- Code Reviewer
- Test Generator
- Documentation Generator

## Flow

```mermaid
flowchart TD
    Requirement["Requirement"]
    Planner["AI Planner"]
    Codex["Codex Implementation"]
    Tests["Automated Tests"]
    Review["AI Review"]
    Human["Human Merge Decision"]

    Requirement --> Planner
    Planner --> Codex
    Codex --> Tests
    Tests --> Review
    Review --> Human
```

## Safety

- AI cannot auto-merge.
- Human approval remains required.
- Failed tests cannot be hidden.
- Production deployment is outside this workflow.

