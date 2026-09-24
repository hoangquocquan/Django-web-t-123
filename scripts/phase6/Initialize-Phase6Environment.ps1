[CmdletBinding()]
param([string]$Path = ".env.phase6")

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Target = Join-Path $Root $Path
if (Test-Path -LiteralPath $Target) {
    throw "Phase 6 environment file already exists; it was not overwritten."
}

function New-RuntimeValue([int]$Bytes) {
    $buffer = [byte[]]::new($Bytes)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($buffer)
    return [Convert]::ToBase64String($buffer).Replace("+", "-").Replace("/", "_").TrimEnd("=")
}

$lines = @(
    "PHASE6_SECRET_KEY=$(New-RuntimeValue 48)",
    "PHASE6_POSTGRES_DB=phase6_portfolio",
    "PHASE6_POSTGRES_USER=phase6_runtime",
    "PHASE6_POSTGRES_PASSWORD=$(New-RuntimeValue 32)",
    "PHASE6_REDIS_PASSWORD=$(New-RuntimeValue 32)",
    "PHASE6_METRICS_BEARER_TOKEN=$(New-RuntimeValue 32)",
    "PHASE6_DJANGO_PORT=8000",
    "PHASE6_VITE_PORT=8443"
)
[System.IO.File]::WriteAllLines($Target, $lines, [System.Text.UTF8Encoding]::new($false))
Write-Output "Created ignored Phase 6 runtime configuration without displaying values."
