"""Create a checksummed PostgreSQL, media, and n8n operations backup."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - fixed local Docker/Git commands only.
import tarfile
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BACKUP_ROOT = PROJECT_ROOT / "backups" / "prod05"
COMPOSE_PROJECT = "mecprecision-vietnam"
HELPER_IMAGE = "postgres:16-alpine"


class BackupError(RuntimeError):
    """Raised when a backup component cannot be captured safely."""


class CommandRunner:
    """Run bounded local commands while keeping credentials out of reports."""

    def run(self, command, *, output_path=None, input_path=None, env=None):
        with ExitStack() as stack:
            capture_output = output_path is None
            stdout = subprocess.PIPE
            stdin = None
            if output_path:
                stdout = stack.enter_context(Path(output_path).open("wb"))
            if input_path:
                stdin = stack.enter_context(Path(input_path).open("rb"))
            completed = subprocess.run(  # nosec B603 - shell is never enabled.
                command,
                stdin=stdin,
                stdout=stdout,
                stderr=subprocess.PIPE,
                check=False,
                env=env,
            )
        if completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", errors="replace")[-1000:]
            raise BackupError(f"Local backup command failed: {detail}")
        if capture_output:
            return completed.stdout.decode("utf-8", errors="replace").strip()
        return ""


def sha256_file(path):
    """Hash an artifact without loading the whole backup into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_release_metadata(runner):
    """Return source/image identifiers only; environment secrets are excluded."""
    commit = runner.run(["git", "rev-parse", "HEAD"])
    image_id = runner.run(
        [
            "docker",
            "image",
            "inspect",
            "mecprecision-vietnam:prod-local",
            "--format",
            "{{.Id}}",
        ]
    )
    return {"git_commit": commit, "image_id": image_id}


def find_container(runner, service):
    output = runner.run(
        [
            "docker",
            "ps",
            "--filter",
            f"label=com.docker.compose.project={COMPOSE_PROJECT}",
            "--filter",
            f"label=com.docker.compose.service={service}",
            "--format",
            "{{.ID}}",
        ]
    )
    container_id = output.splitlines()[0].strip() if output else ""
    if not container_id:
        raise BackupError(f"Running Compose service not found: {service}")
    return container_id


def inspect_container(runner, container_id):
    raw = runner.run(["docker", "inspect", container_id])
    return json.loads(raw)[0]


def container_environment(inspect_payload):
    values = {}
    for item in inspect_payload.get("Config", {}).get("Env", []):
        key, separator, value = item.partition("=")
        if separator:
            values[key] = value
    return values


def named_volume(inspect_payload, destination):
    for mount in inspect_payload.get("Mounts", []):
        if mount.get("Destination") == destination and mount.get("Type") == "volume":
            return mount.get("Name", "")
    raise BackupError(f"Named volume not found for {destination}")


def archive_volume(runner, volume_name, output_path):
    runner.run(
        [
            "docker",
            "run",
            "--rm",
            "--mount",
            f"source={volume_name},target=/source,readonly",
            HELPER_IMAGE,
            "tar",
            "-czf",
            "-",
            "-C",
            "/source",
            ".",
        ],
        output_path=output_path,
    )


def archive_directory(source, output_path):
    with tarfile.open(output_path, "w:gz") as archive:
        if source.exists():
            for path in sorted(source.rglob("*")):
                if path.is_file():
                    archive.add(path, arcname=path.relative_to(source))


def create_backup(output_root=DEFAULT_BACKUP_ROOT, runner=None, now=None):
    """Create one immutable backup package and its sanitized manifest."""
    runner = runner or CommandRunner()
    now = now or datetime.now(UTC)
    package = Path(output_root) / now.strftime("%Y%m%dT%H%M%SZ")
    package.mkdir(parents=True, exist_ok=False)

    database_container = find_container(runner, "database")
    web_container = find_container(runner, "web")
    n8n_container = find_container(runner, "n8n")
    database_inspect = inspect_container(runner, database_container)
    web_inspect = inspect_container(runner, web_container)
    n8n_inspect = inspect_container(runner, n8n_container)
    database_env = container_environment(database_inspect)
    database_name = database_env.get("POSTGRES_DB", "mecprecision")
    database_user = database_env.get("POSTGRES_USER", "mecprecision")

    database_dump = package / "postgres.dump"
    runner.run(
        [
            "docker",
            "exec",
            database_container,
            "pg_dump",
            "-U",
            database_user,
            "-d",
            database_name,
            "-Fc",
            "--no-owner",
            "--no-acl",
        ],
        output_path=database_dump,
    )

    media_archive = package / "media.tar.gz"
    n8n_archive = package / "n8n-data.tar.gz"
    workflow_archive = package / "n8n-workflows.tar.gz"
    archive_volume(
        runner,
        named_volume(web_inspect, "/app/django_backend/media"),
        media_archive,
    )
    archive_volume(
        runner,
        named_volume(n8n_inspect, "/home/node/.n8n"),
        n8n_archive,
    )
    archive_directory(PROJECT_ROOT / "n8n" / "workflows", workflow_archive)

    components = []
    for path, kind in (
        (database_dump, "postgresql_and_n8n_database"),
        (media_archive, "django_media"),
        (n8n_archive, "n8n_encrypted_runtime_config"),
        (workflow_archive, "n8n_versioned_workflows"),
    ):
        components.append(
            {
                "name": path.name,
                "kind": kind,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    manifest = {
        "schema_version": 1,
        "created_at": now.isoformat(),
        "database_engine": "postgresql",
        "database_name": database_name,
        "release": safe_release_metadata(runner),
        "components": components,
        "credentials": "encrypted_or_environment_managed_not_exported_in_plaintext",
        "safety_gates": {
            "human_approval_required": True,
            "auto_merge": False,
            "auto_deploy": False,
            "approval_bypass_detected": False,
        },
    }
    manifest_path = package / "release-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return package, manifest


def main():
    parser = argparse.ArgumentParser(description="Create a PROD-05 operations backup.")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_BACKUP_ROOT)
    args = parser.parse_args()
    package, _manifest = create_backup(output_root=args.output_root)
    print(json.dumps({"status": "BACKUP_COMPLETE", "package": str(package)}))


if __name__ == "__main__":
    main()
