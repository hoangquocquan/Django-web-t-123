# EC2 Simulation

## AWS Concept

EC2 is a virtual server where an application can run with an operating system,
runtime, environment variables, process manager, and network rules.

## Local Equivalent

In this lab, the Django Docker container simulates an EC2 application server.

```text
AWS EC2 instance
-> docker/aws-lab django service
-> Python + Django runtime
```

## Server Lifecycle

| EC2 lifecycle | Local lab command |
| --- | --- |
| Launch instance | `docker compose up django` |
| Stop instance | `docker compose stop django` |
| Replace instance | `docker compose up --build django` |
| View logs | `docker logs mecprecision-aws-lab-django` |

## Environment Variables

The lab passes environment variables into the Django container:

- `DJANGO_SETTINGS_MODULE`
- `SECRET_KEY`
- `DATABASE_URL`
- `LEGACY_DATABASE_URL`
- `AWS_LAB_S3_ENDPOINT_URL`

## Learning Outcome

You can learn how application runtime configuration works before using EC2,
ECS, or Elastic Beanstalk in real AWS.
