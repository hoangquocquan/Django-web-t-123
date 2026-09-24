"""Phase 6D production configuration and operations contract tests."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def test_phase6d_static_gateway_is_single_backend_and_loopback_only():
    compose = (ROOT / "docker-compose.phase6.yml").read_text(encoding="utf-8")
    nginx = (ROOT / "docker" / "phase6" / "nginx.conf").read_text(encoding="utf-8")

    assert "profiles: [phase6d]" in compose
    assert "127.0.0.1:${PHASE6_VITE_PORT:-8443}:8080" in compose
    assert "proxy_pass http://django:8000;" in nginx
    assert "try_files $uri $uri/ /index.html;" in nginx
    assert "phase6-media:/srv/media:ro" in compose


def test_phase6d_images_are_non_root_and_do_not_copy_runtime_secrets():
    backend = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    frontend = (ROOT / "Dockerfile.phase6-frontend").read_text(encoding="utf-8")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert "USER appuser" in backend
    assert "USER 101" in frontend
    assert "rm -rf /app/django_backend/logs" in backend
    assert ".env.*" in dockerignore
    assert "COPY .env" not in backend + frontend


def test_phase6d_startup_and_restore_are_bounded_and_owned():
    start = (ROOT / "scripts" / "phase6" / "Start-Phase6D.ps1").read_text(
        encoding="utf-8"
    )
    drill = (
        ROOT / "scripts" / "phase6" / "Invoke-Phase6DBackupRestoreDrill.ps1"
    ).read_text(encoding="utf-8")
    stop = (ROOT / "scripts" / "phase6" / "Stop-Phase6.ps1").read_text(
        encoding="utf-8"
    )

    assert 'ProjectName = "django-web-t-123-phase6"' in start
    assert '"migrate", "--check"' in start
    assert '"build", "--pull", "django"' in start
    assert '"build", "--pull", "frontend"' in start
    assert "StartupTimeoutSeconds" in start
    assert "phase6_restore_" in drill
    assert "dropdb --if-exists --force" in drill
    assert "Migration fingerprint mismatch after restore" in drill
    assert '"--profile", "phase6d"' in stop
    assert "prune" not in (start + drill).lower()
