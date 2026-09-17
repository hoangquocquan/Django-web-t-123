[CmdletBinding()]
param([string]$EnvironmentFile = ".env.phase6")

$ErrorActionPreference = "Stop"
$ProjectName = "django-web-t-123-phase6"
$Container = "django-web-t-123-phase6-postgres"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$EvidenceDirectory = Join-Path $Root ".phase6\backup-restore"
$Stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$HostDump = Join-Path $EvidenceDirectory "phase6-$Stamp.dump"
$RestoreDatabase = "phase6_restore_$([DateTime]::UtcNow.ToString('yyyyMMddHHmmss'))"
$ContainerDump = "/tmp/phase6d-$Stamp.dump"

function Invoke-Docker([string[]]$Arguments) {
    & docker @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Docker operation failed closed." }
}

function Invoke-PostgresShell([string]$Command) {
    Invoke-Docker @("exec", "-e", "RESTORE_DATABASE=$RestoreDatabase", $Container, "sh", "-ceu", $Command)
}

New-Item -ItemType Directory -Path $EvidenceDirectory -Force | Out-Null
$status = (& docker inspect --format '{{.State.Health.Status}}' $Container 2>$null)
if ($LASTEXITCODE -ne 0 -or $status -ne "healthy") {
    throw "The Phase 6-owned PostgreSQL container must be healthy before the drill."
}

$restoreCreated = $false
# The generated path contains only a fixed prefix and UTC digits. Credentials
# remain inside the container environment and never enter host arguments.
$dumpCommand = 'pg_dump --format=custom --no-owner --no-acl --file="' + $ContainerDump + '" --username="$POSTGRES_USER" "$POSTGRES_DB"'
Invoke-Docker @("exec", $Container, "sh", "-ceu", $dumpCommand)

try {
    Invoke-Docker @("cp", "${Container}:${ContainerDump}", $HostDump)
    if (-not (Test-Path -LiteralPath $HostDump) -or (Get-Item -LiteralPath $HostDump).Length -le 0) {
        throw "Backup artifact was not created."
    }

    Invoke-PostgresShell 'createdb --username="$POSTGRES_USER" "$RESTORE_DATABASE"'
    $restoreCreated = $true
    $restoreCommand = 'pg_restore --exit-on-error --no-owner --no-acl --username="$POSTGRES_USER" --dbname="$RESTORE_DATABASE" "' + $ContainerDump + '"'
    Invoke-PostgresShell $restoreCommand

    $sourceFingerprint = (& docker exec $Container sh -ceu 'psql --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --tuples-only --no-align --command="SELECT md5(string_agg(app || '':'' || name, '','' ORDER BY app, name)) FROM django_migrations;"')
    if ($LASTEXITCODE -ne 0) { throw "Source migration fingerprint failed." }
    $restoreFingerprint = (& docker exec -e "RESTORE_DATABASE=$RestoreDatabase" $Container sh -ceu 'psql --username="$POSTGRES_USER" --dbname="$RESTORE_DATABASE" --tuples-only --no-align --command="SELECT md5(string_agg(app || '':'' || name, '','' ORDER BY app, name)) FROM django_migrations;"')
    if ($LASTEXITCODE -ne 0) { throw "Restored migration fingerprint failed." }
    $restoredTables = (& docker exec -e "RESTORE_DATABASE=$RestoreDatabase" $Container sh -ceu 'psql --username="$POSTGRES_USER" --dbname="$RESTORE_DATABASE" --tuples-only --no-align --command="SELECT count(*) FROM information_schema.tables WHERE table_schema=''public'';"')
    if ($LASTEXITCODE -ne 0 -or [int]$restoredTables -le 0) { throw "Restored schema is not readable." }
    if ($sourceFingerprint.Trim() -ne $restoreFingerprint.Trim()) { throw "Migration fingerprint mismatch after restore." }

    [ordered]@{
        result = "PASS"
        completed_at_utc = [DateTime]::UtcNow.ToString("o")
        backup_file = Split-Path -Leaf $HostDump
        backup_bytes = (Get-Item -LiteralPath $HostDump).Length
        restored_public_tables = [int]$restoredTables
        migration_fingerprint_match = $true
        restore_target = "temporary database in Phase 6-owned PostgreSQL container"
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $EvidenceDirectory "latest-result.json") -Encoding UTF8
    Write-Output "PASS: Phase 6 backup was restored to an isolated temporary database and verified."
} finally {
    if ($restoreCreated) {
        try { Invoke-PostgresShell 'dropdb --if-exists --force --username="$POSTGRES_USER" "$RESTORE_DATABASE"' } catch { }
    }
    try { Invoke-Docker @("exec", $Container, "rm", "-f", $ContainerDump) } catch { }
}
