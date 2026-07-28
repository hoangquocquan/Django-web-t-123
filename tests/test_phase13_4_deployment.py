import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase13_4_deploy import simulate_deployment
from scripts.phase13_4_health_check import validate_health
from scripts.phase13_4_rollback import simulate_rollback
from scripts.phase_validator import validate_phase


DOCS = PROJECT_ROOT / "docs"
DEPLOYMENT = DOCS / "deployment"
N8N = DOCS / "n8n"
REVIEWS = DOCS / "reviews"


def read(path):
    return Path(path).read_text(encoding="utf-8")


def test_deployment_artifacts_exist():
    required = [
        DOCS / "codex-prompts" / "PHASE_13.4_DEPLOYMENT_AUTOMATION.md",
        DEPLOYMENT / "DEPLOYMENT_ARCHITECTURE.md",
        DEPLOYMENT / "DEPLOYMENT_RUNBOOK.md",
        DEPLOYMENT / "DEPLOYMENT_SECURITY.md",
        N8N / "N8N_DEPLOYMENT_WORKFLOW.md",
        PROJECT_ROOT / "scripts" / "phase13_4_deploy.py",
        PROJECT_ROOT / "scripts" / "phase13_4_health_check.py",
        PROJECT_ROOT / "scripts" / "phase13_4_rollback.py",
        REVIEWS / "PHASE_13.4_DEPLOYMENT_REPORT.md",
    ]

    for path in required:
        assert path.exists(), f"Missing deployment artifact: {path}"
        assert path.stat().st_size > 0


def test_deployment_script_dry_run_safety(tmp_path):
    result = simulate_deployment(output_path=tmp_path / "deployment_result.json", dry_run=True)

    assert result["status"] == "DEPLOYMENT_SIMULATION_COMPLETE"
    assert result["environment"] == "local_simulation"
    assert result["safety"]["production_deployed"] is False
    assert result["safety"]["cloud_infrastructure_created"] is False
    assert result["safety"]["production_secrets_stored"] is False
    assert result["safety"]["rollback_capability_removed"] is False


def test_health_check_dry_run_safety(tmp_path):
    deployment_path = tmp_path / "deployment_result.json"
    simulate_deployment(output_path=deployment_path, dry_run=True)
    result = validate_health(
        deployment_path=deployment_path,
        output_path=tmp_path / "health_result.json",
        dry_run=True,
    )

    assert result["status"] == "HEALTH_VALIDATION_COMPLETE"
    assert result["critical_dependencies"]["application_endpoint"] is True
    assert result["critical_dependencies"]["database_connection"] is True
    assert result["safety"]["production_deployed"] is False


def test_rollback_dry_run_safety(tmp_path):
    deployment_path = tmp_path / "deployment_result.json"
    simulate_deployment(output_path=deployment_path, dry_run=True)
    result = simulate_rollback(
        deployment_path=deployment_path,
        output_path=tmp_path / "rollback_result.json",
        dry_run=True,
    )

    assert result["status"] == "ROLLBACK_SIMULATION_COMPLETE"
    assert result["safety"]["production_rollback_executed"] is False
    assert result["safety"]["cloud_infrastructure_modified"] is False
    assert result["safety"]["rollback_capability_preserved"] is True


def test_safety_rules_are_documented():
    architecture = read(DEPLOYMENT / "DEPLOYMENT_ARCHITECTURE.md")
    runbook = read(DEPLOYMENT / "DEPLOYMENT_RUNBOOK.md")
    security = read(DEPLOYMENT / "DEPLOYMENT_SECURITY.md")
    n8n = read(N8N / "N8N_DEPLOYMENT_WORKFLOW.md")

    assert "Production deployment is intentionally out of scope" in architecture
    assert "does not deploy production" in runbook
    assert "production deployed: false" in security
    assert "Do not add production deployment nodes" in n8n


def test_phase_validator_knows_phase13_4(tmp_path):
    result = validate_phase(phase="13.4", output_path=tmp_path / "phase_validation_result.json")

    assert result["phase"] == "13.4"
    assert result["safety"]["auto_deploy"] is False
    assert result["safety"]["auto_approve_production"] is False
