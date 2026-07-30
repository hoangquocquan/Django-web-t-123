import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FACTORY_V2 = PROJECT_ROOT / "ai-factory" / "v2_roles.py"


def load_v2():
    spec = importlib.util.spec_from_file_location("factory_v2_roles", FACTORY_V2)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_factory_v2_roles_are_complete():
    module = load_v2()
    role_keys = {role.key for role in module.ROLES}

    assert {
        "requirement_analyzer",
        "architecture_planner",
        "code_reviewer",
        "test_generator",
        "security_reviewer",
        "documentation_generator",
    }.issubset(role_keys)


def test_factory_v2_run_keeps_human_approval(tmp_path):
    module = load_v2()
    result = module.run_factory_v2("Build Business AI Wave 2", output_path=tmp_path / "factory_v2_result.json")

    assert result["decision"] == "WAITING_FOR_HUMAN_APPROVAL"
    assert result["safety"]["production_deployed"] is False
    assert result["safety"]["code_auto_merged"] is False
    assert result["safety"]["external_ai_api_used"] is False
    assert all(step["human_approval_required"] for step in result["roles"])


def test_factory_v2_documentation_exists():
    docs = (PROJECT_ROOT / "docs" / "ai-factory" / "AI_SOFTWARE_FACTORY_V2.md").read_text(encoding="utf-8")

    assert "Requirement Analyzer" in docs
    assert "Human approval" in docs
    assert "No production deployment" in docs
