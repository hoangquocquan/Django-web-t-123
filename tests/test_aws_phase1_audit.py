from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AWS_AUDIT_DIR = PROJECT_ROOT / "docs" / "aws-audit"
REVIEWS_DIR = PROJECT_ROOT / "docs" / "reviews"
EVIDENCE = PROJECT_ROOT / "ai-factory" / "evidence" / "aws_phase_1.json"


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def test_aws_audit_documents_exist():
    required = [
        "AWS_COMPUTE_AUDIT.md",
        "AWS_DATABASE_AUDIT.md",
        "AWS_STORAGE_AUDIT.md",
        "AWS_NETWORK_AUDIT.md",
        "AWS_SECURITY_AUDIT.md",
        "AWS_CICD_AUDIT.md",
        "AWS_MONITORING_AUDIT.md",
        "AWS_CURRENT_ARCHITECTURE.md",
        "DJANGO_AWS_READINESS_REPORT.md",
    ]

    for filename in required:
        assert (AWS_AUDIT_DIR / filename).exists()


def test_aws_audit_declares_no_real_resource_change():
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    assert payload["aws_resources_created"] is False
    assert payload["aws_resources_modified"] is False
    assert payload["production_deployed"] is False
    assert payload["database_modified"] is False


def test_aws_current_architecture_has_diagram_and_recommendation():
    content = read_text(AWS_AUDIT_DIR / "AWS_CURRENT_ARCHITECTURE.md")

    assert "mermaid" in content
    assert "ECS Fargate" in content
    assert "RDS PostgreSQL" in content


def test_django_readiness_mentions_required_production_gaps():
    content = read_text(AWS_AUDIT_DIR / "DJANGO_AWS_READINESS_REPORT.md")

    assert "Gunicorn" in content
    assert "S3" in content
    assert "RDS PostgreSQL" in content


def test_final_review_report_exists():
    content = read_text(REVIEWS_DIR / "AWS_ARCHITECTURE_AUDIT_FINAL_REPORT.md")

    assert "AWS_ARCHITECTURE_AUDIT_COMPLETE" in content
    assert "No real AWS infrastructure evidence was found" in content
