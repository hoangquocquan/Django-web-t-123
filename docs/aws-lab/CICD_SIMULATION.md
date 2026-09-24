# CI/CD Simulation

## AWS Concept

CI/CD builds, tests, and deploys application changes. In AWS this often means:

```text
GitHub Actions -> ECR -> ECS / Elastic Beanstalk / EC2
```

## Local Lab Equivalent

Workflow:

`.github/workflows/aws-lab-ci.yml`

## Pipeline Flow

```mermaid
flowchart LR
    PUSH["Git push"] --> TEST["Run tests"]
    TEST --> COMPOSE["Validate Docker Compose"]
    COMPOSE --> BUILD["Build Django lab image"]
    BUILD --> REVIEW["Human review"]
```

## What It Does Not Do

- It does not push to ECR.
- It does not deploy ECS.
- It does not create AWS resources.
- It does not spend money.

## Learning Outcome

You learn the shape of a deployment pipeline safely before connecting AWS.
