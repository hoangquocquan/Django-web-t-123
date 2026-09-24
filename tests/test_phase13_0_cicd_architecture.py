from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS = PROJECT_ROOT / "docs"
CICD = DOCS / "cicd"
REVIEWS = DOCS / "reviews"


REQUIRED_DOCUMENTS = [
    CICD / "CICD_ARCHITECTURE_DESIGN.md",
    CICD / "BRANCHING_STRATEGY.md",
    CICD / "ENVIRONMENT_STRATEGY.md",
    CICD / "PIPELINE_STAGES.md",
    CICD / "DEPLOYMENT_STRATEGY.md",
    CICD / "CICD_SECURITY_MODEL.md",
    CICD / "AI_CICD_INTEGRATION.md",
    REVIEWS / "PHASE_13.0_CICD_ARCHITECTURE_REPORT.md",
    DOCS / "codex-prompts" / "PHASE_13.0_CICD_ARCHITECTURE_DESIGN.md",
]


def read(path):
    return Path(path).read_text(encoding="utf-8")


def test_required_documents_exist():
    for path in REQUIRED_DOCUMENTS:
        assert path.exists(), f"Missing CI/CD document: {path}"
        assert path.stat().st_size > 0


def test_architecture_complete():
    content = read(CICD / "CICD_ARCHITECTURE_DESIGN.md")

    assert "Pipeline Overview" in content
    assert "Development Flow" in content
    assert "Testing Flow" in content
    assert "Build Flow" in content
    assert "Deployment Flow" in content
    assert "Rollback Flow" in content
    assert "Phase 13.0 is architecture design only" in content


def test_security_documented():
    content = read(CICD / "CICD_SECURITY_MODEL.md")

    assert "Never commit `.env` files" in content
    assert "Use least privilege" in content
    assert "AI and n8n cannot approve production" in content
    assert "Audit Logs" in content


def test_rollback_documented():
    deployment = read(CICD / "DEPLOYMENT_STRATEGY.md")
    report = read(REVIEWS / "PHASE_13.0_CICD_ARCHITECTURE_REPORT.md")

    assert "Blue/Green" in deployment
    assert "Rollback" in deployment
    assert "previous artifact" in report
    assert "Database rollback requires" in report


def test_ai_integration_has_human_boundary():
    content = read(CICD / "AI_CICD_INTEGRATION.md")

    assert "Ollama" in content
    assert "n8n" in content
    assert "AI can recommend. Humans decide." in content
    assert "deploy production automatically" in content

