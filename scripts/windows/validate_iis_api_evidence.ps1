param(
    [string]$EvidencePath = "docs\migration\production_evidence\input\iis_api_evidence.csv"
)

$ErrorActionPreference = "Stop"

function Write-JsonResult {
    param([hashtable]$Result)
    $Result | ConvertTo-Json -Depth 8
}

try {
    if (-not (Test-Path $EvidencePath)) {
        Write-JsonResult @{
            status = "IIS_EVIDENCE_INCOMPLETE"
            evidence_path = $EvidencePath
            rows = 0
            legacy_rows = 0
            django_rows = 0
            csv_readable = $false
            errors = @("Evidence CSV does not exist.")
        }
        exit 0
    }

    $rows = @(Import-Csv -Path $EvidencePath -ErrorAction Stop)
    $legacyRows = @($rows | Where-Object { $_.endpoint -like "/api/*" -and $_.endpoint -notlike "/api/v1/*" })
    $djangoRows = @($rows | Where-Object { $_.endpoint -like "/api/v1/*" })
    $apiRows = @($rows | Where-Object { $_.endpoint -like "/api/*" })
    $errors = @()

    if ($rows.Count -eq 0) {
        $errors += "Evidence CSV has no rows."
    }
    if ($apiRows.Count -eq 0) {
        $errors += "No API endpoints were found in the evidence CSV."
    }
    if ($djangoRows.Count -eq 0) {
        $errors += "No Django /api/v1 endpoints were found in the evidence CSV."
    }

    Write-JsonResult @{
        status = if ($errors.Count -eq 0) { "IIS_EVIDENCE_READY" } else { "IIS_EVIDENCE_INCOMPLETE" }
        evidence_path = $EvidencePath
        rows = $rows.Count
        legacy_rows = $legacyRows.Count
        django_rows = $djangoRows.Count
        legacy_endpoints_detected = $legacyRows.Count -gt 0
        django_endpoints_detected = $djangoRows.Count -gt 0
        csv_readable = $true
        errors = $errors
    }
    exit 0
} catch {
    Write-JsonResult @{
        status = "IIS_EVIDENCE_INCOMPLETE"
        evidence_path = $EvidencePath
        rows = 0
        legacy_rows = 0
        django_rows = 0
        csv_readable = $false
        errors = @($_.Exception.Message)
    }
    exit 0
}
