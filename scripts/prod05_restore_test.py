"""Validate a PROD-05 backup by restoring only into isolated resources."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tarfile
import tempfile
import uuid
from pathlib import Path

try:
    from scripts.prod05_backup import (
        BackupError,
        CommandRunner,
        container_environment,
        find_container,
        inspect_container,
        sha256_file,
    )
except ModuleNotFoundError:  # Chay truc tiep tu thu muc scripts.
    from prod05_backup import (  # type: ignore[no-redef]
        BackupError,
        CommandRunner,
        container_environment,
        find_container,
        inspect_container,
        sha256_file,
    )


def validate_manifest(package):
    manifest_path = Path(package) / "release-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise BackupError("Unsupported backup manifest schema.")
    required_gates = {
        "human_approval_required": True,
        "auto_merge": False,
        "auto_deploy": False,
        "approval_bypass_detected": False,
    }
    if manifest.get("safety_gates") != required_gates:
        raise BackupError("Backup safety gates are missing or malformed.")
    for component in manifest.get("components", []):
        path = Path(package) / component["name"]
        if not path.is_file() or sha256_file(path) != component["sha256"]:
            raise BackupError(f"Backup checksum mismatch: {component['name']}")
    return manifest


def safe_extract(archive_path, target):
    """Extract an archive after rejecting links and path traversal."""
    target = Path(target).resolve()
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            destination = (target / member.name).resolve()
            if (
                member.issym()
                or member.islnk()
                or target not in destination.parents
                and destination != target
            ):
                raise BackupError("Unsafe path found in backup archive.")
        archive.extractall(target, filter="data")
    return sum(1 for path in target.rglob("*") if path.is_file())


def restore_database_test(package, runner):
    database_container = find_container(runner, "database")
    web_container = find_container(runner, "web")
    database_env = container_environment(inspect_container(runner, database_container))
    database_user = database_env.get("POSTGRES_USER", "mecprecision")
    database_name = "prod05_restore_" + uuid.uuid4().hex[:12]
    if not re.fullmatch(r"[a-z0-9_]+", database_name):
        raise BackupError("Generated restore database name is invalid.")
    dump_path = Path(package) / "postgres.dump"
    runner.run(
        [
            "docker",
            "exec",
            database_container,
            "createdb",
            "-U",
            database_user,
            database_name,
        ]
    )
    try:
        runner.run(
            [
                "docker",
                "exec",
                "-i",
                database_container,
                "pg_restore",
                "-U",
                database_user,
                "-d",
                database_name,
                "--no-owner",
                "--no-acl",
            ],
            input_path=dump_path,
        )
        shell = (
            'export DATABASE_URL="${DATABASE_URL%/*}/$RESTORE_DATABASE_NAME"; '
            "python manage.py migrate --check; "
            'python manage.py shell -c "from django.db import connection; '
            "connection.ensure_connection(); print('RESTORE_DB_SMOKE_OK')\""
        )
        output = runner.run(
            [
                "docker",
                "exec",
                "-e",
                f"RESTORE_DATABASE_NAME={database_name}",
                web_container,
                "sh",
                "-c",
                shell,
            ]
        )
        if "RESTORE_DB_SMOKE_OK" not in output:
            raise BackupError("Restored database smoke test did not complete.")
        return {"migration_check": "PASS", "database_smoke": "PASS"}
    finally:
        runner.run(
            [
                "docker",
                "exec",
                database_container,
                "dropdb",
                "-U",
                database_user,
                "--if-exists",
                database_name,
            ]
        )


def run_restore_test(package, runner=None):
    runner = runner or CommandRunner()
    package = Path(package).resolve()
    manifest = validate_manifest(package)
    with tempfile.TemporaryDirectory(
        prefix="mecprecision-prod05-restore-"
    ) as temporary:
        temporary = Path(temporary)
        media_files = safe_extract(package / "media.tar.gz", temporary / "media")
        n8n_files = safe_extract(package / "n8n-data.tar.gz", temporary / "n8n")
        workflow_files = safe_extract(
            package / "n8n-workflows.tar.gz", temporary / "workflows"
        )
        database = restore_database_test(package, runner)
        shutil.rmtree(temporary, ignore_errors=True)
    return {
        "status": "RESTORE_TEST_PASS",
        "manifest_schema": manifest["schema_version"],
        "database": database,
        "files": {
            "media": media_files,
            "n8n_runtime": n8n_files,
            "n8n_workflows": workflow_files,
        },
        "isolated_restore": True,
        "production_data_modified": False,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Restore-test a PROD-05 backup package."
    )
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_restore_test(args.package)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
