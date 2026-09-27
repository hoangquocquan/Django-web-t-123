$ErrorActionPreference = "Stop"

$repo = "C:\Users\hoang\Documents\Codex\n8n-line-uat-demo"
$expectedBranch = "feature/n8n-line-uat-demo"
$expectedN8nVersion = "2.37.10"
$workflowId = "uatAiSalesLineApprovalDemo"
$runtimePointer = "C:\Users\hoang\Documents\Codex\line-uat-current-runtime.txt"

function Test-StrictTrue {
    param([AllowNull()][string]$Value)
    return -not [string]::IsNullOrWhiteSpace($Value) -and
        $Value.Trim().Equals("true", [StringComparison]::OrdinalIgnoreCase)
}

Set-Location -LiteralPath $repo
if ((git branch --show-current).Trim() -ne $expectedBranch) {
    throw "SAFETY STOP: wrong branch."
}
foreach ($scope in @("Process", "User", "Machine")) {
    if (Test-StrictTrue ([Environment]::GetEnvironmentVariable("LINE_SEND_ENABLED", $scope))) {
        throw "SAFETY STOP: LINE_SEND_ENABLED=true detected."
    }
}
if (-not (Test-Path -LiteralPath $runtimePointer -PathType Leaf)) {
    throw "SAFETY STOP: isolated runtime pointer was not found."
}

$runtimeRoot = [IO.File]::ReadAllText($runtimePointer).Trim()
$statePath = Join-Path $runtimeRoot "runtime-state.json"
$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
if ($state.repo -ne $repo -or $state.branch -ne $expectedBranch) {
    throw "SAFETY STOP: runtime identity does not match this worktree."
}
$workflowPath = [string]$state.workflow
$n8nRoot = Join-Path $runtimeRoot "n8n"
$n8nDatabase = Join-Path $n8nRoot ".n8n\database.sqlite"
$logRoot = Join-Path $runtimeRoot "logs"
if (-not (Test-Path -LiteralPath $workflowPath -PathType Leaf)) {
    throw "SAFETY STOP: runtime workflow was not found."
}
$workflow = Get-Content -LiteralPath $workflowPath -Raw | ConvertFrom-Json
if ($workflow.id -ne $workflowId -or $workflow.active -ne $false) {
    throw "SAFETY STOP: runtime workflow identity or active state is invalid."
}

$ownerHelper = Join-Path $repo "scripts\line_uat\n8n_owner_project.py"
$projectOutput = @(& python $ownerHelper resolve $n8nDatabase)
if ($LASTEXITCODE -ne 0 -or $projectOutput.Count -ne 1) {
    throw "N8N OWNER PROJECT NOT READY"
}
$projectId = [string]$projectOutput[0]
if ($projectId -notmatch '^[A-Za-z0-9_-]{8,64}$') {
    throw "SAFETY STOP: invalid n8n owner project identifier."
}

Import-Module (Join-Path $repo "scripts\line_uat\N8nCliResolver.psm1") -Force
$n8nCli = Resolve-N8nCli -Repo $repo `
    -ProcessOverridePath ([Environment]::GetEnvironmentVariable("N8N_UAT_CLI_PATH", "Process")) `
    -UserOverridePath ([Environment]::GetEnvironmentVariable("N8N_UAT_CLI_PATH", "User")) `
    -ExpectedVersion $expectedN8nVersion

$protectedTokenPath = Join-Path $runtimeRoot "foundation-token.dpapi"
if (-not (Test-Path -LiteralPath $protectedTokenPath -PathType Leaf)) {
    throw "SAFETY STOP: protected Foundation token was not found."
}
$foundationSecure = ConvertTo-SecureString (
    Get-Content -LiteralPath $protectedTokenPath -Raw
)
$tokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($foundationSecure)
try {
    $foundationToken = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPointer)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPointer)
}
if ([string]::IsNullOrWhiteSpace($foundationToken)) {
    throw "SAFETY STOP: protected Foundation token could not be restored."
}

$processTable = @(Get-CimInstance Win32_Process)
$processIds = [Collections.Generic.List[int]]::new()
[void]$processIds.Add([int]$state.n8n_pid)
do {
    $foundChild = $false
    foreach ($process in $processTable) {
        if ($processIds.Contains([int]$process.ParentProcessId) -and
            -not $processIds.Contains([int]$process.ProcessId)) {
            [void]$processIds.Add([int]$process.ProcessId)
            $foundChild = $true
        }
    }
} while ($foundChild)
if (-not (Get-Process -Id ([int]$state.n8n_pid) -ErrorAction SilentlyContinue)) {
    throw "SAFETY STOP: recorded isolated n8n process is not running."
}

$importArguments = @($n8nCli.PrefixArguments) + @(
    "import:workflow",
    "--input=$workflowPath",
    "--projectId=$projectId",
    "--activeState=false"
)
& $n8nCli.FilePath @importArguments | Out-File `
    -LiteralPath (Join-Path $logRoot "n8n-owner-import.log") -Encoding utf8
if ($LASTEXITCODE -ne 0) { throw "n8n owner-project workflow import failed." }

foreach ($processId in @($processIds | Sort-Object -Descending)) {
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
}
$shutdownDeadline = (Get-Date).AddSeconds(15)
do {
    Start-Sleep -Milliseconds 250
    $oldN8nListening = Test-NetConnection -ComputerName 127.0.0.1 -Port 5678 `
        -InformationLevel Quiet -WarningAction SilentlyContinue
} while ($oldN8nListening -and (Get-Date) -lt $shutdownDeadline)
if ($oldN8nListening) {
    throw "SAFETY STOP: previous isolated n8n process did not stop."
}

$env:LINE_SEND_ENABLED = "false"
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

$startArguments = @($n8nCli.PrefixArguments) + @("start")
$processArguments = @($startArguments | ForEach-Object {
    if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ }
})
$n8n = Start-Process -FilePath $n8nCli.FilePath -ArgumentList $processArguments `
    -WorkingDirectory $repo `
    -RedirectStandardOutput (Join-Path $logRoot "n8n-owner-attached.stdout.log") `
    -RedirectStandardError (Join-Path $logRoot "n8n-owner-attached.stderr.log") `
    -WindowStyle Hidden -PassThru

$env:DJANGO_UAT_BEARER_TOKEN = $null
$foundationToken = $null
$foundationSecure.Dispose()
[GC]::Collect()

$deadline = (Get-Date).AddSeconds(45)
do {
    Start-Sleep -Milliseconds 500
    $n8nReady = Test-NetConnection -ComputerName 127.0.0.1 -Port 5678 `
        -InformationLevel Quiet -WarningAction SilentlyContinue
} while (-not $n8nReady -and (Get-Date) -lt $deadline)
if (-not $n8nReady) {
    Stop-Process -Id $n8n.Id -Force -ErrorAction SilentlyContinue
    throw "n8n restart after owner-project import failed."
}

$verifyOutput = @(& python $ownerHelper verify $n8nDatabase $projectId)
if ($LASTEXITCODE -ne 0 -or $verifyOutput -notcontains "WORKFLOW_OWNER_ATTACHMENT_READY=yes") {
    Stop-Process -Id $n8n.Id -Force -ErrorAction SilentlyContinue
    throw "SAFETY STOP: workflow owner attachment verification failed."
}

$state.n8n_pid = $n8n.Id
$state | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding utf8
$projectId = $null
$projectOutput = $null

Write-Output "N8N_OWNER_PROJECT_READY=yes"
Write-Output "WORKFLOW_IMPORTED=yes"
Write-Output "WORKFLOW_OWNER_ATTACHMENT_READY=yes"
Write-Output "N8N_LISTENING_127_0_0_1_5678=yes"
Write-Output "LINE_SEND_ENABLED=false"
Write-Output "WORKFLOW_ACTIVE=false"
