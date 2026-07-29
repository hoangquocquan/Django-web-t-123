from pathlib import Path
import re

import pytest
from django.test import Client


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAB_DIR = PROJECT_ROOT / "docker" / "aws-lab"
DOCS_DIR = PROJECT_ROOT / "docs" / "aws-lab"
COMPOSE = LAB_DIR / "docker-compose.aws-lab.yml"
NGINX = LAB_DIR / "nginx" / "default.conf"
WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "aws-lab-ci.yml"
EVIDENCE = PROJECT_ROOT / "ai-factory" / "evidence" / "aws_learning_phase_2.json"


def text(path):
    return Path(path).read_text(encoding="utf-8")


def service_block(compose_text, service_name):
    pattern = rf"(?ms)^  {re.escape(service_name)}:\n(.*?)(?=^  [a-zA-Z0-9_-]+:|\nnetworks:|\nvolumes:|\Z)"
    match = re.search(pattern, compose_text)
    assert match, f"Missing service {service_name}"
    return match.group(1)


def test_django_reachable_through_test_client():
    response = Client().get("/api/v1/health/")

    assert response.status_code == 200


def test_docker_services_are_defined():
    content = text(COMPOSE)

    for service in ["django", "postgres", "minio", "nginx"]:
        assert service_block(content, service)
    assert "django-blue" in content
    assert "profiles:" in content


def test_database_connection_simulates_rds():
    content = text(COMPOSE)
    postgres = service_block(content, "postgres")
    django = service_block(content, "django")

    assert "postgres:16-alpine" in postgres
    assert "POSTGRES_DB: mecprecision_lab" in postgres
    assert "DATABASE_URL: postgresql://" in django


def test_storage_connection_simulates_s3():
    content = text(COMPOSE)
    minio = service_block(content, "minio")
    django = service_block(content, "django")

    assert "minio/minio" in minio
    assert "9001:9001" in minio
    assert "AWS_LAB_S3_ENDPOINT_URL" in django
    assert "AWS_LAB_S3_BUCKET" in django


def test_nginx_routing_simulates_load_balancer():
    content = text(NGINX)

    assert "upstream django_app" in content
    assert "proxy_pass http://django_app" in content
    assert "/health" in content


def test_github_actions_simulates_cicd():
    content = text(WORKFLOW)

    assert "Validate Docker Compose syntax" in content
    assert "Build Django lab image" in content
    assert "pytest tests/test_aws_learning_lab.py" in content


def test_learning_docs_exist_and_map_aws_concepts():
    required = [
        "EC2_SIMULATION.md",
        "RDS_SIMULATION.md",
        "S3_SIMULATION.md",
        "LOAD_BALANCER_SIMULATION.md",
        "CICD_SIMULATION.md",
        "AWS_SECURITY_SIMULATION.md",
        "AWS_LEARNING_ARCHITECTURE.md",
    ]
    for filename in required:
        assert (DOCS_DIR / filename).exists()

    architecture = text(DOCS_DIR / "AWS_LEARNING_ARCHITECTURE.md")
    assert "EC2 / ECS" in architecture
    assert "RDS PostgreSQL" in architecture
    assert "S3" in architecture


def test_evidence_declares_no_real_aws_usage():
    content = text(EVIDENCE)

    assert '"aws_resources_created": false' in content
    assert '"aws_account_required": false' in content
    assert '"paid_cloud_services_used": false' in content
