import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path):
    """Read a Wave 4 artifact."""
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_wave4_reports_exist_and_state_no_legacy_deletion():
    required_reports = [
        "docs/django-migration/WAVE4_LEGACY_DEPENDENCY_AUDIT.md",
        "docs/django-migration/WAVE4_PAYMENT_DECISION.md",
        "docs/django-migration/WAVE4_DATABASE_OWNERSHIP_REPORT.md",
        "docs/django-migration/WAVE4_LEGACY_RETIREMENT_PLAN.md",
        "docs/reviews/WAVE_4_DJANGO_FINAL_OWNERSHIP_REVIEW.md",
        "docs/reviews/WAVE_4_DJANGO_LEGACY_REDUCTION_FINAL_REPORT.md",
    ]

    for report in required_reports:
        content = read_text(report)
        assert content.strip()

    review = read_text("docs/reviews/WAVE_4_DJANGO_FINAL_OWNERSHIP_REVIEW.md")
    assert "Legacy deletion: false" in review
    assert "Destructive migration: false" in review


def test_wave4_payment_decision_requires_future_project():
    content = read_text("docs/django-migration/WAVE4_PAYMENT_DECISION.md")

    assert "REQUIRE_FUTURE_PROJECT" in content
    assert "Wave 4 does not migrate payment" in content


def test_wave4_database_report_classifies_ownership():
    content = read_text("docs/django-migration/WAVE4_DATABASE_OWNERSHIP_REPORT.md")

    assert "DJANGO_OWNED" in content
    assert "SHARED" in content
    assert "LEGACY_ONLY" in content
    assert "PARTIALLY_FINALIZED" in content


def test_wave4_retirement_plan_requires_human_approval():
    content = read_text("docs/django-migration/WAVE4_LEGACY_RETIREMENT_PLAN.md")

    assert "Human architecture approval" in content
    assert "Rollback Plan" in content


def test_wave4_evidence_safety_flags():
    evidence = json.loads(read_text("ai-factory/evidence/django_wave_4.json"))

    assert evidence["legacy_preserved"] is True
    assert evidence["production_shutdown"] is False
    assert evidence["legacy_deleted"] is False
    assert evidence["destructive_migration"] is False
    assert evidence["payment_migrated"] is False
    assert evidence["human_approval_required"] is True
    assert evidence["expected_status"] == "DJANGO_FINAL_OWNERSHIP_ASSESSMENT_COMPLETE"
