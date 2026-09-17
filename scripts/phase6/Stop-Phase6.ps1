[CmdletBinding()]
param(
    [string]$EnvironmentFile = ".env.phase6",
    [switch]$RemoveOwnedVolumes
)

$ErrorActionPreference = "Stop"
$ProjectName = "django-web-t-123-phase6"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$StatePath = Join-Path $Root ".phase6\vite-process.json"

if (Test-Path -LiteralPath $StatePath) {
    $state = Get-Content -Raw -LiteralPath $StatePath | ConvertFrom-Json
    $process = Get-Process -Id ([int]$state.pid) -ErrorAction SilentlyContinue
    if ($process) {
        if ($process.ProcessName -ne "node" -or $process.StartTime.ToUniversalTime().Ticks -ne [long]$state.startTicks) {
            throw "Recorded Vite process ownership is ambiguous; no process was stopped."
        }
        Stop-Process -Id $process.Id -Force
        $process.WaitForExit(10000)
    }
    Remove-Item -LiteralPath $StatePath -Force
}

$arguments = @(
    "compose", "-p", $ProjectName, "--env-file", $EnvironmentFile,
    "-f", "docker-compose.phase6.yml", "--profile", "phase6d",
    "down", "--timeout", "15"
)
if ($RemoveOwnedVolumes) { $arguments += "--volumes" }
$docker = Start-Process -FilePath "docker" -ArgumentList $arguments -WorkingDirectory $Root -PassThru -NoNewWindow
if (-not $docker.WaitForExit(60000)) {
    Stop-Process -Id $docker.Id -Force -ErrorAction SilentlyContinue
    throw "Timed out stopping Phase 6-owned Compose resources."
}
if ($docker.ExitCode -ne 0) { throw "Failed to stop Phase 6-owned Compose resources." }
Write-Output "Stopped only resources owned by django-web-t-123-phase6."
