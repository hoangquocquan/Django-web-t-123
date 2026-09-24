from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEWS = PROJECT_ROOT / "docs" / "reviews"
PROMPTS = PROJECT_ROOT / "docs" / "codex-prompts"


BASELINE_DOCUMENTS = [
    PROMPTS / "PHASE_12_SYSTEM_BASELINE_AND_AUDIT.md",
    REVIEWS / "PHASE_12_SYSTEM_ARCHITECTURE_BASELINE.md",
    REVIEWS / "PHASE_12_CODEBASE_AUDIT_REPORT.md",
    REVIEWS / "PHASE_12_API_BASELINE.md",
    REVIEWS / "PHASE_12_DATABASE_BASELINE.md",
    REVIEWS / "PHASE_12_SECURITY_BASELINE.md",
    REVIEWS / "PHASE_12_TESTING_BASELINE.md",
    REVIEWS / "PHASE_12_SYSTEM_BASELINE_REPORT.md",
]


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def test_baseline_documents_exist():
    for document in BASELINE_DOCUMENTS:
        assert document.exists(), f"Missing Phase 12 baseline document: {document}"
        assert document.stat().st_size > 0


def test_reports_generated_with_expected_sections():
    required_sections = {
        "PHASE_12_SYSTEM_ARCHITECTURE_BASELINE.md": "Before And After Migration Comparison",
        "PHASE_12_CODEBASE_AUDIT_REPORT.md": "Technical Debt",
        "PHASE_12_API_BASELINE.md": "Active APIs",
        "PHASE_12_DATABASE_BASELINE.md": "Archive Status",
        "PHASE_12_SECURITY_BASELINE.md": "Known Risks",
        "PHASE_12_TESTING_BASELINE.md": "Known Missing Tests",
        "PHASE_12_SYSTEM_BASELINE_REPORT.md": "Master Audit Dashboard",
    }

    for filename, heading in required_sections.items():
        assert heading in read_text(REVIEWS / filename)


def test_phase11_completion_recognized():
    combined_reports = "\n".join(read_text(document) for document in BASELINE_DOCUMENTS)

    assert "TRAINING_SHUTDOWN_COMPLETE" in combined_reports
    assert "DATABASE_ARCHIVE_COMPLETE" in combined_reports
    assert "BLOCKED_SAFELY" in combined_reports


def test_no_modification_executed():
    report = read_text(REVIEWS / "PHASE_12_SYSTEM_BASELINE_REPORT.md")

    assert "No production behavior was modified." in report
    assert "No routes were changed." in report
    assert "No database schema" in report
    assert "No deployment was executed." in report
