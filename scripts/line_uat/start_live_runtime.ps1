$ErrorActionPreference = "Stop"

$repo = "C:\Users\hoang\Documents\Codex\n8n-line-uat-demo"
$expectedBranch = "feature/n8n-line-uat-demo"
$credentialNames = @(
    "LINE_UAT_CHANNEL_ACCESS_TOKEN",
    "LINE_UAT_CHANNEL_SECRET",
    "LINE_UAT_RECIPIENT_USER_ID"
)

function Test-StrictTrue {
    param([AllowNull()][string]$Value)
    return -not [string]::IsNullOrWhiteSpace($Value) -and
        $Value.Trim().Equals("true", [StringComparison]::OrdinalIgnoreCase)
}

Set-Location -LiteralPath $repo
$branch = (git branch --show-current).Trim()
if ($branch -ne $expectedBranch) { throw "SAFETY STOP: wrong branch." }

$credentialValues = @{}
foreach ($name in $credentialNames) {
    $value = [Environment]::GetEnvironmentVariable($name, "User")
    $configured = -not [string]::IsNullOrWhiteSpace($value)
    $status = if ($configured) { "yes" } else { "no" }
    Write-Output "${name}: configured=${status}"
    if (-not $configured) { throw "SAFETY STOP: required LINE UAT credential is missing." }
    $credentialValues[$name] = $value.Trim()
}

foreach ($scope in @("User", "Machine")) {
    if (Test-StrictTrue ([Environment]::GetEnvironmentVariable("LINE_SEND_ENABLED", $scope))) {
        throw "SAFETY STOP: persistent LINE_SEND_ENABLED=true detected."
    }
}

$recipient = $credentialValues["LINE_UAT_RECIPIENT_USER_ID"]
if ($recipient -notmatch '^U[0-9a-fA-F]{32}$') {
    throw "SAFETY STOP: configured recipient is not a LINE user ID."
}

$profileHeaders = @{ Authorization = "Bearer $($credentialValues['LINE_UAT_CHANNEL_ACCESS_TOKEN'])" }
try {
    $profileResponse = Invoke-WebRequest -UseBasicParsing -Method Get `
        -Uri ("https://api.line.me/v2/bot/profile/" + $recipient) `
        -Headers $profileHeaders -TimeoutSec 15
    if ($profileResponse.StatusCode -ne 200) { throw "Profile verification did not return HTTP 200." }
    Write-Output "LINE_UAT_RECIPIENT_PROFILE: verified=yes"
}
catch {
    throw "SAFETY STOP: LINE UAT recipient/profile verification failed. No message was sent."
}
finally {
    $profileHeaders = $null
    $profileResponse = $null
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$runtimeRoot = "C:\Users\hoang\Documents\Codex\line-uat-live-runtime-$stamp"
$n8nRoot = Join-Path $runtimeRoot "n8n"
$logRoot = Join-Path $runtimeRoot "logs"
$dbPath = Join-Path $runtimeRoot "django-uat.sqlite3"
$workflowPath = Join-Path $runtimeRoot "line-uat-live-interlocked.json"
New-Item -ItemType Directory -Path $runtimeRoot, $n8nRoot, $logRoot -Force | Out-Null

$workflowBuilder = Join-Path $repo "scripts\line_uat\build_live_workflow.py"
$sourceWorkflow = Join-Path $repo "automation\n8n\line_uat_approval_demo.json"
& python $workflowBuilder $sourceWorkflow $workflowPath
if ($LASTEXITCODE -ne 0) { throw "Failed to build runtime-only interlocked workflow." }

$env:DATABASE_URL = "sqlite:///" + ($dbPath -replace '\\', '/')
$env:ALLOWED_HOSTS = "localhost,127.0.0.1"
$env:DEBUG = "false"
$env:LINE_SEND_ENABLED = "false"
foreach ($name in $credentialNames) {
    [Environment]::SetEnvironmentVariable($name, $credentialValues[$name], "Process")
}

python django_backend/manage.py migrate --noinput | Out-File `
    -LiteralPath (Join-Path $logRoot "django-migrate.log") -Encoding utf8
if ($LASTEXITCODE -ne 0) { throw "Django migration failed." }

$bootstrapHelper = Join-Path $repo "scripts\line_uat\bootstrap_foundation_uat.py"
$bootstrapOutput = @(& python $bootstrapHelper)
if ($LASTEXITCODE -ne 0 -or $bootstrapOutput -notcontains "FOUNDATION_UAT_ROLE_READY=yes") {
    throw "Failed to bootstrap the least-privilege Foundation UAT role."
}
Write-Output "FOUNDATION_UAT_ROLE_READY=yes"

$tokenHelper = Join-Path $repo "scripts\line_uat\create_foundation_token.py"
$tokenOutput = @(& python $tokenHelper)
if ($LASTEXITCODE -ne 0 -or $tokenOutput.Count -eq 0) { throw "Failed to create temporary Foundation token." }
$foundationToken = [string]$tokenOutput[-1]
if ([string]::IsNullOrWhiteSpace($foundationToken)) { throw "Failed to capture temporary Foundation token." }
$foundationSecure = ConvertTo-SecureString $foundationToken -AsPlainText -Force
$foundationProtected = ConvertFrom-SecureString $foundationSecure
[IO.File]::WriteAllText((Join-Path $runtimeRoot "foundation-token.dpapi"), $foundationProtected, [Text.Encoding]::UTF8)
Write-Output "FOUNDATION_UAT_TOKEN_READY=yes"

$django = Start-Process -FilePath "python" `
    -ArgumentList @("django_backend/manage.py", "runserver", "127.0.0.1:8000", "--noreload") `
    -WorkingDirectory $repo `
    -RedirectStandardOutput (Join-Path $logRoot "django-false.stdout.log") `
    -RedirectStandardError (Join-Path $logRoot "django-false.stderr.log") `
    -WindowStyle Hidden -PassThru

foreach ($name in $credentialNames) { [Environment]::SetEnvironmentVariable($name, $null, "Process") }
$credentialValues.Clear()
$recipient = $null

$env:N8N_USER_FOLDER = $n8nRoot
$env:N8N_HOST = "127.0.0.1"
$env:N8N_PORT = "5678"
$env:N8N_PROTOCOL = "http"
$env:N8N_SECURE_COOKIE = "false"
$env:N8N_DIAGNOSTICS_ENABLED = "false"
$env:N8N_VERSION_NOTIFICATIONS_ENABLED = "false"
$env:N8N_TEMPLATES_ENABLED = "false"
$env:N8N_PERSONALIZATION_ENABLED = "false"
$env:N8N_BLOCK_ENV_ACCESS_IN_NODE = "false"
$env:DJANGO_UAT_BASE_URL = "http://127.0.0.1:8000"
$env:DJANGO_UAT_BEARER_TOKEN = $foundationToken

n8n import:workflow --input=$workflowPath | Out-File `
    -LiteralPath (Join-Path $logRoot "n8n-import.log") -Encoding utf8
if ($LASTEXITCODE -ne 0) {
    Stop-Process -Id $django.Id -Force -ErrorAction SilentlyContinue
    throw "n8n workflow import failed."
}

$n8n = Start-Process -FilePath "n8n.cmd" -ArgumentList @("start") `
    -WorkingDirectory $repo `
    -RedirectStandardOutput (Join-Path $logRoot "n8n.stdout.log") `
    -RedirectStandardError (Join-Path $logRoot "n8n.stderr.log") `
    -WindowStyle Hidden -PassThru

$env:DJANGO_UAT_BEARER_TOKEN = $null
$foundationToken = $null
$foundationSecure.Dispose()
$foundationProtected = $null
$tokenOutput = $null
[GC]::Collect()

$deadline = (Get-Date).AddSeconds(45)
do {
    Start-Sleep -Milliseconds 500
    $djangoReady = Test-NetConnection -ComputerName 127.0.0.1 -Port 8000 -InformationLevel Quiet -WarningAction SilentlyContinue
    $n8nReady = Test-NetConnection -ComputerName 127.0.0.1 -Port 5678 -InformationLevel Quiet -WarningAction SilentlyContinue
} while ((-not $djangoReady -or -not $n8nReady) -and (Get-Date) -lt $deadline)

if (-not $djangoReady -or -not $n8nReady) {
    Stop-Process -Id $django.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $n8n.Id -Force -ErrorAction SilentlyContinue
    throw "Runtime startup failed. Review sanitized logs in the runtime directory."
}

$state = [ordered]@{
    runtime_root = $runtimeRoot
    repo = $repo
    database = $dbPath
    workflow = $workflowPath
    django_pid = $django.Id
    n8n_pid = $n8n.Id
    branch = $branch
}
$state | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimeRoot "runtime-state.json") -Encoding utf8
[IO.File]::WriteAllText("C:\Users\hoang\Documents\Codex\line-uat-current-runtime.txt", $runtimeRoot, [Text.Encoding]::UTF8)

Write-Output "RUNTIME_UAT_READY=yes"
Write-Output "DJANGO_LISTENING_127_0_0_1_8000=yes"
Write-Output "N8N_LISTENING_127_0_0_1_5678=yes"
Write-Output "LINE_SEND_ENABLED=false"
Write-Output "WORKFLOW_ACTIVE=false"
Write-Output "RUNTIME_ROOT=$runtimeRoot"
