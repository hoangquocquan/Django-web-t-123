# Load Balancer Simulation

## AWS Concept

An AWS Application Load Balancer receives HTTP/HTTPS traffic and forwards it to
healthy application targets.

## Local Equivalent

This lab uses Nginx:

```text
AWS Application Load Balancer
-> Nginx container
```

## Reverse Proxy

Nginx listens on:

```text
http://localhost:8088/
```

and forwards requests to:

```text
django:8000
```

## Multiple Django Instances Concept

The compose file includes an optional `django-blue` profile. This demonstrates
how multiple application instances can exist behind a proxy.

Command:

```bash
docker compose -f docker/aws-lab/docker-compose.aws-lab.yml --profile scale-demo up --build
```

## Health Check

Nginx exposes:

```text
/health -> /api/v1/health/
```

## Learning Outcome

You can learn reverse proxy and target health concepts before using ALB.
