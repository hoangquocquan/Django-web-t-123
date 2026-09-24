"""AI Software Factory V2 role orchestration.

V2 tach ro cac vai tro review de nguoi hoc thay moi buoc lam gi. Module nay
khong tu sua code, khong merge, khong approve production. No chi tao ke hoach,
nhan xet va yeu cau con nguoi xac nhan.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "ai-factory" / "results" / "factory_v2_result.json"


@dataclass(frozen=True)
class FactoryRole:
    """Mo ta mot vai tro trong AI Software Factory."""

    key: str
    title: str
    responsibility: str

    def run(self, requirement):
        """Tra ve ket qua review dang deterministic de test on dinh."""
        return {
            "role": self.key,
            "title": self.title,
            "status": "READY_FOR_HUMAN_REVIEW",
            "summary": f"{self.title} reviewed requirement: {requirement[:120]}",
            "responsibility": self.responsibility,
            "human_approval_required": True,
        }


ROLES = [
    FactoryRole("requirement_analyzer", "Requirement Analyzer", "Clarify scope, risks, and acceptance criteria."),
    FactoryRole("architecture_planner", "Architecture Planner", "Plan modules, dependencies, and rollback boundaries."),
    FactoryRole("code_reviewer", "Code Reviewer", "Review code quality, maintainability, and regressions."),
    FactoryRole("test_generator", "Test Generator", "Suggest unit, integration, and safety tests."),
    FactoryRole("security_reviewer", "Security Reviewer", "Check secrets, permissions, and unsafe automation."),
    FactoryRole("documentation_generator", "Documentation Generator", "Create concise docs for operators and developers."),
]


def utc_now():
    """Tra ve timestamp UTC cho evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_factory_v2(requirement, output_path=DEFAULT_OUTPUT):
    """Chay luong V2 va ghi report local."""
    steps = [role.run(requirement) for role in ROLES]
    result = {
        "version": "v2",
        "created_at": utc_now(),
        "requirement": requirement,
        "flow": [
            "Requirement",
            "AI Planner",
            "Codex Development",
            "Automated Tests",
            "AI Code Review",
            "Security Review",
            "Human Approval",
        ],
        "roles": steps,
        "decision": "WAITING_FOR_HUMAN_APPROVAL",
        "safety": {
            "production_deployed": False,
            "code_auto_merged": False,
            "external_ai_api_used": False,
            "human_approval_required": True,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    """Entrypoint demo cho AI Factory V2."""
    result = run_factory_v2("Complete Business + AI Wave 2 platform capabilities.")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

