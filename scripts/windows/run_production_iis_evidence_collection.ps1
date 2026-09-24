param(
    [string]$LogRoot = "C:\inetpub\logs\LogFiles",
    [string]$OutputPath = "docs\migration\production_evidence\input\iis_api_evidence.csv",
    [string]$CollectionPeriod = "",
    [string]$PythonCommand = "python"
)

$ErrorActionPreference = "Stop"

function Invoke-JsonStep {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    try {
        $raw = & $Command
        $parsed = $null
        try {
            $parsed = $raw | ConvertFrom-Json -ErrorAction Stop
        } catch {
            $parsed = @{ raw_output = $raw }
        }
        return [pscustomobject]@{
            name = $Name
            status = "STEP_COMPLETED"
            output = $parsed
            errors = @()
        }
    } catch {
        return [pscustomobject]@{
            name = $Name
            status = "STEP_FAILED"
            output = $null
            errors = @($_.Exception.Message)
        }
    }
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptRoot "..\..")
$detectScript = Join-Path $scriptRoot "detect_iis_site.ps1"
$diagnoseScript = Join-Path $scriptRoot "diagnose_iis_evidence.ps1"
$exportScript = Join-Path $scriptRoot "export_iis_api_evidence.ps1"
$validatorScript = Join-Path $projectRoot "scripts\phase11_1_6_5_1_collection_validator.py"

$steps = @()
$steps += Invoke-JsonStep -Name "detect_iis_site" -Command {
    powershell -ExecutionPolicy Bypass -File $detectScript
}
$steps += Invoke-JsonStep -Name "diagnose_iis_evidence" -Command {
    powershell -ExecutionPolicy Bypass -File $diagnoseScript -LogRoot $LogRoot
}
$steps += Invoke-JsonStep -Name "export_iis_api_evidence" -Command {
    powershell -ExecutionPolicy Bypass -File $exportScript -LogRoot $LogRoot -OutputPath $OutputPath
}

$validatorArgs = @($validatorScript)
if (-not [string]::IsNullOrWhiteSpace($CollectionPeriod)) {
    $validatorArgs += "--period"
    $validatorArgs += $CollectionPeriod
}

$steps += Invoke-JsonStep -Name "collection_validator" -Command {
    & $PythonCommand @validatorArgs
}

$validatorStep = $steps | Where-Object { $_.name -eq "collection_validator" } | Select-Object -First 1
$validatorOutput = $validatorStep.output
$decision = if ($validatorOutput -and $validatorOutput.status) {
    $validatorOutput.status
} else {
    "INCOMPLETE_EVIDENCE_PACKAGE"
}

@{
    status = if ($decision -eq "COMPLETE_EVIDENCE_PACKAGE") { "PRODUCTION_IIS_EVIDENCE_READY" } else { "PRODUCTION_IIS_EVIDENCE_INCOMPLETE" }
    log_root = $LogRoot
    output_csv = $OutputPath
    collection_period = if ([string]::IsNullOrWhiteSpace($CollectionPeriod)) { "NOT_PROVIDED" } else { $CollectionPeriod }
    steps = $steps
    decision = $decision
    safety = @{
        shutdown_executed = $false
        legacy_api_disabled = $false
        iis_modified = $false
        proxy_modified = $false
        routes_changed = $false
        database_modified = $false
    }
} | ConvertTo-Json -Depth 12
