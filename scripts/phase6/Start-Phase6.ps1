[CmdletBinding()]
param(
    [ValidateRange(1, 65535)][int]$DjangoPort = 8000,
    [ValidateRange(1, 65535)][int]$VitePort = 8443,
    [ValidateRange(30, 300)][int]$StartupTimeoutSeconds = 120,
    [string]$EnvironmentFile = ".env.phase6"
)

$ErrorActionPreference = "Stop"
$ProjectName = "django-web-t-123-phase6"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ComposeFile = Join-Path $Root "docker-compose.phase6.yml"
$EnvironmentPath = Join-Path $Root $EnvironmentFile
$StateDirectory = Join-Path $Root ".phase6"
$LogDirectory = Join-Path $StateDirectory "logs"
$ViteStatePath = Join-Path $StateDirectory "vite-process.json"
$RequiredNames = @(
    "PHASE6_SECRET_KEY", "PHASE6_POSTGRES_DB", "PHASE6_POSTGRES_USER",
    "PHASE6_POSTGRES_PASSWORD", "PHASE6_REDIS_PASSWORD",
    "PHASE6_METRICS_BEARER_TOKEN"
)

function Write-SanitizedResult([string]$Code, [string]$Message) {
    [ordered]@{ code = $Code; message = $Message; project = $ProjectName } |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $LogDirectory "startup-result.json") -Encoding UTF8
    Write-Output "$Code`: $Message"
}

function Invoke-BoundedProcess {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [int]$TimeoutSeconds,
        [string]$LogName
    )
    $stdout = Join-Path $LogDirectory "$LogName.out.log"
    $stderr = Join-Path $LogDirectory "$LogName.err.log"
    $process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -WorkingDirectory $Root `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        throw "timeout:$LogName"
    }
    if ($process.ExitCode -ne 0) { throw "failed:$LogName" }
}

function Test-ConfiguredPort([int]$Port, [string]$Label) {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
    if ($listeners.Count -gt 0) {
        Write-Output "$Label port $Port is occupied. No owning process was inspected or modified."
        throw "port_collision:$Label"
    }
    Write-Output "$Label port $Port is empty."
}

function Wait-Http {
    param([string]$Uri, [int]$TimeoutSeconds, [string]$Label)
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

function Stop-OwnedPartialStartup {
    if (Test-Path -LiteralPath $ViteStatePath) {
        try {
            $state = Get-Content -Raw -LiteralPath $ViteStatePath | ConvertFrom-Json
            $process = Get-Process -Id ([int]$state.pid) -ErrorAction SilentlyContinue
            if ($process -and $process.ProcessName -eq "node" -and $process.StartTime.ToUniversalTime().Ticks -eq [long]$state.startTicks) {
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            }
        } catch { }
    }
    try {
        Invoke-BoundedProcess "docker" @("compose", "-p", $ProjectName, "--env-file", $EnvironmentFile, "-f", "docker-compose.phase6.yml", "down", "--timeout", "15") 30 "cleanup"
    } catch { }
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

    $composeSource = Get-Content -Raw -LiteralPath $ComposeFile
    foreach ($ownedName in @("name: django-web-t-123-phase6", "django-web-t-123-phase6-internal")) {
        if (-not $composeSource.Contains($ownedName)) { throw "ownership_validation_failed" }
    }

    Test-ConfiguredPort $DjangoPort "Django"
    Test-ConfiguredPort $VitePort "Vite"
    $env:PHASE6_DJANGO_PORT = [string]$DjangoPort
    $env:PHASE6_VITE_PORT = [string]$VitePort

    $compose = @("compose", "-p", $ProjectName, "--env-file", $EnvironmentFile, "-f", "docker-compose.phase6.yml")
    # Compose may create dependencies before `up --wait` returns, so cleanup
    # ownership begins immediately before this first mutating command.
    $started = $true
    # Always build from the current checkout. Reusing a previously tagged
    # Phase 6 image can omit newly added management commands or backend code.
    Invoke-BoundedProcess "docker" ($compose + @("build", "django")) $StartupTimeoutSeconds "django-build"
    Invoke-BoundedProcess "docker" ($compose + @("up", "-d", "--wait", "--wait-timeout", [string]$StartupTimeoutSeconds, "postgres", "redis")) ($StartupTimeoutSeconds + 15) "dependencies"
    Invoke-BoundedProcess "docker" ($compose + @("run", "--rm", "django", "python", "manage.py", "migrate", "--noinput")) $StartupTimeoutSeconds "migrate"
    Invoke-BoundedProcess "docker" ($compose + @("run", "--rm", "django", "python", "manage.py", "migrate", "--check")) $StartupTimeoutSeconds "migrate-check"
    Invoke-BoundedProcess "docker" ($compose + @("up", "-d", "--wait", "--wait-timeout", [string]$StartupTimeoutSeconds, "django")) ($StartupTimeoutSeconds + 15) "django"

    $node = (Get-Command node -ErrorAction Stop).Source
    $viteCli = Join-Path $Root "figma_make_frontend\node_modules\vite\bin\vite.js"
    if (-not (Test-Path -LiteralPath $viteCli -PathType Leaf)) { throw "configuration_missing:frontend_dependencies" }
    $env:VITE_DJANGO_ORIGIN = "http://127.0.0.1:$DjangoPort"
    $quotedViteCli = '"' + $viteCli + '"'
    $viteOut = Join-Path $LogDirectory "vite.out.log"
    $viteErr = Join-Path $LogDirectory "vite.err.log"
    $vite = Start-Process -FilePath $node -ArgumentList @($quotedViteCli) -WorkingDirectory (Join-Path $Root "figma_make_frontend") `
        -RedirectStandardOutput $viteOut -RedirectStandardError $viteErr -PassThru -WindowStyle Hidden
    @{ pid = $vite.Id; startTicks = $vite.StartTime.ToUniversalTime().Ticks } |
        ConvertTo-Json | Set-Content -LiteralPath $ViteStatePath -Encoding UTF8

    Wait-Http "http://127.0.0.1:$DjangoPort/api/v1/phase6/live/" $StartupTimeoutSeconds "django_liveness"
    Wait-Http "http://127.0.0.1:$DjangoPort/api/v1/phase6/ready/" $StartupTimeoutSeconds "django_readiness"
    Wait-Http "http://127.0.0.1:$VitePort/" $StartupTimeoutSeconds "vite"

    $loginBody = '{"email":"phase6-route-probe@example.invalid","password":"not-a-credential"}'
    try {
        Invoke-WebRequest -UseBasicParsing -Method Post -Uri "http://127.0.0.1:$VitePort/api/v1/foundation/auth/login/" `
            -ContentType "application/json" -Body $loginBody -TimeoutSec 5 | Out-Null
    } catch {
        if (-not $_.Exception.Response -or [int]$_.Exception.Response.StatusCode -eq 404) { throw "smoke_failed:login_route" }
    }
    try {
        Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$VitePort/api/v1/canonical/rfqs/" -TimeoutSec 5 | Out-Null
    } catch {
        if (-not $_.Exception.Response -or [int]$_.Exception.Response.StatusCode -eq 404) { throw "smoke_failed:canonical_rfq_route" }
    }
    Write-SanitizedResult "ready" "Phase 6A Django, PostgreSQL, Redis, and Vite passed bounded readiness and routing smoke checks."
} catch {
    $code = ("$($_.Exception.Message)" -split ':', 2)[0]
    if ($started) { Stop-OwnedPartialStartup }
    Write-SanitizedResult $code "Phase 6A startup failed closed. Inspect task-owned sanitized logs."
    exit 1
}
