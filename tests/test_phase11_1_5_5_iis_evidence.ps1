$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$ExportScript = Join-Path $ProjectRoot "scripts\windows\export_iis_api_evidence.ps1"
$ValidateScript = Join-Path $ProjectRoot "scripts\windows\validate_iis_api_evidence.ps1"

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) {
        throw $Message
    }
}

function Invoke-JsonScript {
    param([string]$Command)
    $output = Invoke-Expression $Command
    return ($output | ConvertFrom-Json)
}

$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("mecprecision-iis-test-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force $TempRoot | Out-Null

try {
    $missingRoot = Join-Path $TempRoot "missing"
    $missingCsv = Join-Path $TempRoot "missing.csv"
    $missingResult = Invoke-JsonScript "powershell -ExecutionPolicy Bypass -File `"$ExportScript`" -LogRoot `"$missingRoot`" -OutputPath `"$missingCsv`""
    Assert-True ($missingResult.status -eq "IIS_EVIDENCE_INCOMPLETE") "Missing IIS logs should be incomplete."

    $emptyRoot = Join-Path $TempRoot "empty"
    New-Item -ItemType Directory -Force $emptyRoot | Out-Null
    $emptyCsv = Join-Path $TempRoot "empty.csv"
    $emptyResult = Invoke-JsonScript "powershell -ExecutionPolicy Bypass -File `"$ExportScript`" -LogRoot `"$emptyRoot`" -OutputPath `"$emptyCsv`""
    Assert-True ($emptyResult.status -eq "IIS_EVIDENCE_INCOMPLETE") "Empty log folder should be incomplete."

    $logRoot = Join-Path $TempRoot "logs\W3SVC1"
    New-Item -ItemType Directory -Force $logRoot | Out-Null
    $logFile = Join-Path $logRoot "u_ex260801.log"
    @"
#Software: Microsoft Internet Information Services
#Version: 1.0
#Fields: date time s-ip cs-method cs-uri-stem cs-uri-query s-port cs-username c-ip cs(User-Agent) sc-status
2026-08-01 10:00:00 127.0.0.1 GET /api/products - 443 - 10.0.0.10 Mozilla 200
2026-08-01 10:01:00 127.0.0.1 GET /api/v1/catalog/products/ - 443 - 10.0.0.11 Mozilla 200
"@ | Set-Content -Path $logFile -Encoding UTF8

    $validCsv = Join-Path $TempRoot "iis_api_evidence.csv"
    $validResult = Invoke-JsonScript "powershell -ExecutionPolicy Bypass -File `"$ExportScript`" -LogRoot `"$TempRoot\logs`" -OutputPath `"$validCsv`""
    Assert-True ($validResult.status -eq "IIS_EVIDENCE_EXPORTED") "Valid IIS log should export evidence."
    Assert-True ($validResult.legacy_rows -eq 1) "Legacy API row should be detected."
    Assert-True ($validResult.django_rows -eq 1) "Django API row should be detected."

    $validation = Invoke-JsonScript "powershell -ExecutionPolicy Bypass -File `"$ValidateScript`" -EvidencePath `"$validCsv`""
    Assert-True ($validation.status -eq "IIS_EVIDENCE_READY") "Valid exported CSV should be ready."
    Assert-True ($validation.legacy_endpoints_detected -eq $true) "Validator should detect legacy endpoint rows."
    Assert-True ($validation.django_endpoints_detected -eq $true) "Validator should detect Django endpoint rows."

    "PHASE_11.1.5.5_IIS_EVIDENCE_TEST_PASSED"
} finally {
    if (Test-Path $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force
    }
}
