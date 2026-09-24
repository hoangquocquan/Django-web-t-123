[CmdletBinding()]
param(
    [ValidateRange(1, 65535)][int]$DjangoPort = 8001,
    [ValidateRange(1, 65535)][int]$FrontendPort = 8443,
    [ValidateRange(60, 600)][int]$StartupTimeoutSeconds = 240,
    [string]$EnvironmentFile = ".env.phase6"
)

$ErrorActionPreference = "Stop"
$ProjectName = "django-web-t-123-phase6"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$EnvironmentPath = Join-Path $Root $EnvironmentFile
$LogDirectory = Join-Path $Root ".phase6\logs"
$RequiredNames = @(
    "PHASE6_SECRET_KEY", "PHASE6_POSTGRES_DB", "PHASE6_POSTGRES_USER",
    "PHASE6_POSTGRES_PASSWORD", "PHASE6_REDIS_PASSWORD",
    "PHASE6_METRICS_BEARER_TOKEN"
)

function Invoke-BoundedProcess {
    param([string[]]$Arguments, [int]$TimeoutSeconds, [string]$LogName)
    $stdout = Join-Path $LogDirectory "$LogName.out.log"
    $stderr = Join-Path $LogDirectory "$LogName.err.log"
    $process = Start-Process -FilePath "docker" -ArgumentList $Arguments -WorkingDirectory $Root `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        throw "timeout:$LogName"
    }
    if ($process.ExitCode -ne 0) { throw "failed:$LogName" }
}

function Test-FreePort([int]$Port, [string]$Label) {
    $probe = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
    try {
        $probe.Start()
    } catch [System.Net.Sockets.SocketException] {
        throw "port_collision:$Label"
    } finally {
        $probe.Stop()
    }
}

function Wait-Http([string]$Uri, [int]$TimeoutSeconds, [string]$Label) {
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) { return }
        } catch { }
        Start-Sleep -Milliseconds 750
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "readiness_timeout:$Label"
}

New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
$started = $false
try {
    if (-not (Test-Path -LiteralPath $EnvironmentPath -PathType Leaf)) {
        throw "configuration_missing:environment_file"
    }
    $definedNames = Get-Content -LiteralPath $EnvironmentPath |
        Where-Object { $_ -match '^\s*[A-Za-z_][A-Za-z0-9_]*\s*=' } |
        ForEach-Object { ($_ -split '=', 2)[0].Trim() }
    foreach ($name in $RequiredNames) {
        if ($name -notin $definedNames) { throw "configuration_missing:$name" }
    }

    Test-FreePort $DjangoPort "Django"
    Test-FreePort $FrontendPort "frontend"
    $env:PHASE6_DJANGO_PORT = [string]$DjangoPort
    $env:PHASE6_VITE_PORT = [string]$FrontendPort
    $compose = @(
        "compose", "-p", $ProjectName, "--env-file", $EnvironmentFile,
        "-f", "docker-compose.phase6.yml", "--profile", "phase6d"
    )

    $started = $true
    # Build sequentially because Docker Desktop/BuildKit can corrupt its session
    # header when two builds share this Unicode workspace path concurrently.
    Invoke-BoundedProcess ($compose + @("build", "--pull", "django")) $StartupTimeoutSeconds "phase6d-build-django"
    Invoke-BoundedProcess ($compose + @("build", "--pull", "frontend")) $StartupTimeoutSeconds "phase6d-build-frontend"
    Invoke-BoundedProcess ($compose + @("up", "-d", "--wait", "--wait-timeout", [string]$StartupTimeoutSeconds, "postgres", "redis")) ($StartupTimeoutSeconds + 15) "phase6d-dependencies"
    Invoke-BoundedProcess ($compose + @("run", "--rm", "django", "python", "manage.py", "migrate", "--noinput")) $StartupTimeoutSeconds "phase6d-migrate"
    Invoke-BoundedProcess ($compose + @("run", "--rm", "django", "python", "manage.py", "migrate", "--check")) $StartupTimeoutSeconds "phase6d-migrate-check"
    Invoke-BoundedProcess ($compose + @("up", "-d", "--wait", "--wait-timeout", [string]$StartupTimeoutSeconds, "django", "frontend")) ($StartupTimeoutSeconds + 15) "phase6d-runtime"

    Wait-Http "http://127.0.0.1:$DjangoPort/api/v1/phase6/live/" $StartupTimeoutSeconds "django_liveness"
    Wait-Http "http://127.0.0.1:$FrontendPort/api/v1/phase6/ready/" $StartupTimeoutSeconds "gateway_readiness"
    Wait-Http "http://127.0.0.1:$FrontendPort/" $StartupTimeoutSeconds "production_frontend"
    [ordered]@{
        code = "ready"
        project = $ProjectName
        topology = "static-frontend-to-single-django-backend"
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $LogDirectory "phase6d-startup-result.json") -Encoding UTF8
    Write-Output "ready: Phase 6D static frontend, Django, PostgreSQL, and Redis passed bounded startup checks."
} catch {
    if ($started) {
        try {
            Invoke-BoundedProcess @("compose", "-p", $ProjectName, "--env-file", $EnvironmentFile, "-f", "docker-compose.phase6.yml", "--profile", "phase6d", "down", "--timeout", "15") 45 "phase6d-cleanup"
        } catch { }
    }
    $code = ("$($_.Exception.Message)" -split ':', 2)[0]
    Write-Output "$code`: Phase 6D startup failed closed; inspect task-owned logs."
    exit 1
}
