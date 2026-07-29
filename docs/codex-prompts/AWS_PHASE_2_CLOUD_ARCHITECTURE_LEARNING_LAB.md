# AWS Phase 2 - Cloud Architecture Learning Lab

## Objective

Build a local AWS architecture simulation lab using Docker and documentation.

## Scope

- EC2 simulation with Django container.
- RDS simulation with PostgreSQL container.
- S3 simulation with MinIO.
- Load Balancer simulation with Nginx.
- CI/CD simulation with GitHub Actions.
- Security learning documentation.

## DO NOT

- Do not create AWS resources.
- Do not use paid cloud services.
- Do not require an AWS account.
- Do not deploy production.
- Do not modify real infrastructure.

## Implementation Tasks

1. Create `docker/aws-lab/`.
2. Add Docker Compose learning lab.
3. Add Nginx reverse proxy.
4. Add PostgreSQL and MinIO simulation.
5. Add GitHub Actions lab workflow.
6. Add learning documentation and diagrams.
7. Add validation tests.
8. Run AI Factory review.

## Testing Requirements

- `pytest tests/test_aws_learning_lab.py`
- `pytest`
- `python ai-factory/run_ai_factory.py --phase aws-learning-2`

## Git Requirements

- Branch: `feature/aws-learning-lab`
- Commit: `feat: create aws architecture learning lab`
- Tag: `aws-learning-lab-complete`

## Expected Output

Final status: `AWS_LEARNING_LAB_COMPLETE`.
