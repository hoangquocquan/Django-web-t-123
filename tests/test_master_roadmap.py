from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(path):
    """Read a roadmap artifact as UTF-8 text."""
    return path.read_text(encoding="utf-8")


def test_master_roadmap_documents_exist():
    required = [
        PROJECT_ROOT / "docs" / "codex-prompts" / "MASTER_ROADMAP_MEC_PRECISION_DJANGO_AI_BUSINESS_PLATFORM_2026.md",
        PROJECT_ROOT / "docs" / "roadmap" / "MEC_PRECISION_DJANGO_AI_BUSINESS_PLATFORM_2026.md",
        PROJECT_ROOT / "docs" / "roadmap" / "WORKSTREAM_EXECUTION_ORDER.md",
        PROJECT_ROOT / "docs" / "roadmap" / "WORKSTREAM_DEPENDENCY_GRAPH.md",
        PROJECT_ROOT / "docs" / "roadmap" / "WORKSTREAM_BRANCH_STRATEGY.md",
        PROJECT_ROOT / "docs" / "reviews" / "MEC_PRECISION_PLATFORM_MASTER_REPORT.md",
    ]

    for path in required:
        assert path.exists()
        assert path.stat().st_size > 0


def test_master_report_does_not_claim_final_platform_completion():
    report = read(PROJECT_ROOT / "docs" / "reviews" / "MEC_PRECISION_PLATFORM_MASTER_REPORT.md")

    assert "MASTER_ROADMAP_READY" in report
    assert "PARTIALLY_COMPLETE_FOUNDATION_READY" in report
    assert "MEC_PRECISION_DJANGO_AI_BUSINESS_PLATFORM_COMPLETE` must not" in report


def test_all_workstreams_are_listed_with_separate_branches():
    roadmap = read(PROJECT_ROOT / "docs" / "roadmap" / "WORKSTREAM_BRANCH_STRATEGY.md")

    for branch in [
        "feature/frontend-migration",
        "feature/sales-platform",
        "feature/crm-system",
        "feature/ai-sales",
        "feature/ai-document",
        "feature/n8n-automation",
        "feature/ai-factory-v2",
    ]:
        assert branch in roadmap
