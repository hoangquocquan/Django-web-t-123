from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = PROJECT_ROOT / "docs" / "migration" / "IIS_PRODUCTION_EVIDENCE_COLLECTION_CHECKLIST.md"
RUNBOOK = PROJECT_ROOT / "docs" / "migration" / "IIS_PRODUCTION_EVIDENCE_OPERATOR_RUNBOOK.md"
EVIDENCE_ROOT = PROJECT_ROOT / "docs" / "migration" / "production_evidence"
TEMPLATE = EVIDENCE_ROOT / "IIS_COLLECTION_RESULT_TEMPLATE.md"


def read(path):
    return Path(path).read_text(encoding="utf-8")


def test_checklist_exists():
    assert CHECKLIST.exists()
    content = read(CHECKLIST)
    assert "## Server Information" in content
    assert "## IIS Log Verification" in content
    assert "## Log Collection" in content
    assert "## API Analysis" in content
    assert "## Evidence Export" in content


def test_runbook_exists():
    assert RUNBOOK.exists()
    content = read(RUNBOOK)
    for heading in [
        "## Step 1: Connect To Windows Server",
        "## Step 2: Identify IIS Site",
        "## Step 3: Locate W3SVC Logs",
        "## Step 4: Run Diagnostics",
        "## Step 5: Export Evidence",
        "## Step 6: Validate Evidence",
        "## Step 7: Upload Evidence Package",
    ]:
        assert heading in content


def test_evidence_structure_exists():
    assert (EVIDENCE_ROOT / "input").exists()
    assert (EVIDENCE_ROOT / "input" / "iis_logs" / ".gitkeep").exists()
    assert (EVIDENCE_ROOT / "input" / "iis_api_evidence.csv").exists()
    assert (EVIDENCE_ROOT / "reports").exists()
    assert (EVIDENCE_ROOT / "reports" / "REAL_IIS_PRODUCTION_TRAFFIC_REPORT.json").exists()
    assert (EVIDENCE_ROOT / "approvals").exists()


def test_required_fields_documented():
    content = read(CHECKLIST)
    for field in ["date", "time", "c-ip", "cs-uri-stem", "sc-status", "cs(User-Agent)"]:
        assert f"`{field}`" in content


def test_result_template_documents_decision_fields():
    assert TEMPLATE.exists()
    content = read(TEMPLATE)
    for text in [
        "## Collection Period",
        "## Server",
        "## Log Source",
        "Legacy `/api/*` requests",
        "Django `/api/v1/*` requests",
        "Unknown clients",
        "COMPLETE_EVIDENCE_PACKAGE",
        "INCOMPLETE_EVIDENCE_PACKAGE",
    ]:
        assert text in content
