import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase13_1_docker_build import build_image
from scripts.phase13_1_docker_validate import validate_image


DOCS = PROJECT_ROOT / "docs"
DOCKER_DOCS = DOCS / "docker"
REVIEWS = DOCS / "reviews"


def read(path):
    return Path(path).read_text(encoding="utf-8")


def test_docker_files_exist():
    dockerfile = PROJECT_ROOT / "Dockerfile"
    compose = PROJECT_ROOT / "docker-compose.yml"

    assert dockerfile.exists()
    assert compose.exists()
    assert "USER appuser" in read(dockerfile)
    assert "HEALTHCHECK" in read(dockerfile)
    assert "database:" in read(compose)
    assert "mecprecision-local" in read(compose)
    assert "/app/django_backend\n" not in read(compose)


def test_build_scripts_exist():
    assert (PROJECT_ROOT / "scripts" / "phase13_1_docker_build.py").exists()
    assert (PROJECT_ROOT / "scripts" / "phase13_1_docker_validate.py").exists()


def test_reports_generated():
    required = [
        DOCKER_DOCS / "DOCKER_ARCHITECTURE.md",
        DOCKER_DOCS / "DOCKER_SECURITY_CHECKLIST.md",
        DOCKER_DOCS / "docker_build_report.json",
        DOCKER_DOCS / "docker_validation_report.json",
        REVIEWS / "PHASE_13.1_DOCKER_BUILD_REPORT.md",
    ]

    for path in required:
        assert path.exists(), f"Missing Docker artifact: {path}"
        assert path.stat().st_size > 0


def test_no_production_deployment():
    build_report = json.loads((DOCKER_DOCS / "docker_build_report.json").read_text(encoding="utf-8"))
    validation_report = json.loads((DOCKER_DOCS / "docker_validation_report.json").read_text(encoding="utf-8"))

    assert build_report["safety"]["production_deployed"] is False
    assert build_report["safety"]["image_pushed_externally"] is False
    assert build_report["safety"]["real_registry_credentials_used"] is False
    assert validation_report["safety"]["production_deployed"] is False
    assert validation_report["safety"]["image_pushed_externally"] is False


def test_scripts_can_generate_reports_without_deploying(tmp_path):
    build_result = build_image(output_path=tmp_path / "build.json", skip_build=True)
    validation_result = validate_image(output_path=tmp_path / "validate.json", skip_container=True)

    assert build_result["safety"]["production_deployed"] is False
    assert build_result["safety"]["image_pushed_externally"] is False
    assert validation_result["safety"]["production_deployed"] is False
    assert validation_result["safety"]["image_pushed_externally"] is False
