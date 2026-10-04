"""Resolve and verify the single owner project in an isolated n8n UAT database."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

WORKFLOW_ID = "uatAiSalesLineApprovalDemo"


def _connect_read_only(database: Path) -> sqlite3.Connection:
    if not database.is_file():
        raise RuntimeError("SAFETY STOP: isolated n8n database was not found.")
    return sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)


def resolve_owner_project(database: Path) -> str:
    """Return the only enabled owner's personal project or fail closed."""
    with _connect_read_only(database) as connection:
        rows = connection.execute(
            """
            SELECT p.id
            FROM project AS p
            JOIN project_relation AS pr ON pr.projectId = p.id
            JOIN user AS u ON u.id = pr.userId
            WHERE u.roleSlug = 'global:owner'
              AND u.disabled = 0
              AND p.type = 'personal'
              AND p.creatorId = u.id
              AND pr.role = 'project:personalOwner'
            """
        ).fetchall()
    if len(rows) != 1 or not rows[0][0]:
        raise RuntimeError(
            "SAFETY STOP: expected exactly one initialized n8n owner project."
        )
    return str(rows[0][0])


def verify_workflow_ownership(
    database: Path, project_id: str, workflow_id: str = WORKFLOW_ID
) -> None:
    """Verify one inactive workflow owned by the resolved personal project."""
    with _connect_read_only(database) as connection:
        workflow = connection.execute(
            "SELECT active FROM workflow_entity WHERE id = ?",
            (workflow_id,),
        ).fetchall()
        shares = connection.execute(
            """
            SELECT role
            FROM shared_workflow
            WHERE workflowId = ? AND projectId = ?
            """,
            (workflow_id, project_id),
        ).fetchall()
    if workflow != [(0,)]:
        raise RuntimeError(
            "SAFETY STOP: expected exactly one inactive UAT workflow."
        )
    if shares != [("workflow:owner",)]:
        raise RuntimeError(
            "SAFETY STOP: UAT workflow is not owned by the owner project."
        )


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        raise SystemExit(
            "usage: n8n_owner_project.py resolve DB | verify DB PROJECT_ID"
        )
    command = argv[1]
    database = Path(argv[2]).resolve()
    if command == "resolve" and len(argv) == 3:
        print(resolve_owner_project(database))
        return 0
    if command == "verify" and len(argv) == 4:
        verify_workflow_ownership(database, argv[3])
        print("WORKFLOW_OWNER_ATTACHMENT_READY=yes")
        return 0
    raise SystemExit("invalid arguments")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
