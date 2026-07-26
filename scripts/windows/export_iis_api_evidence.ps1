param(
    [string]$LogRoot = "C:\inetpub\logs\LogFiles",
    [string]$OutputPath = "docs\migration\production_evidence\input\iis_api_evidence.csv"
)

$ErrorActionPreference = "Stop"

function New-EvidenceRow {
    param(
        [string]$Timestamp,
        [string]$Source,
        [string]$Client,
        [string]$Endpoint,
        [string]$StatusCode,
        [string]$UserAgent
    )
    [pscustomobject]@{
        timestamp = $Timestamp
        source = $Source
        client = $Client
        endpoint = $Endpoint
        status_code = $StatusCode
        user_agent = $UserAgent
    }
}

function Ensure-OutputFile {
    param([string]$Path, [object[]]$Rows)
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force $parent | Out-Null
    }
    if ($Rows.Count -eq 0) {
        "timestamp,source,client,endpoint,status_code,user_agent" | Set-Content -Path $Path -Encoding UTF8
        return
    }
    $Rows | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
}

function Add-Error {
    param([string]$Message)
    if (-not [string]::IsNullOrWhiteSpace($Message)) {
        $script:errors += $Message
    }
}

function Get-FieldValue {
    param([hashtable]$Map, [string]$Name)
    if ($Map.ContainsKey($Name)) {
        return $Map[$Name]
    }
    return "-"
}

$rows = @()
$errors = @()
$logFiles = @()
$filesWithFields = 0
$filesMissingUriField = 0
$invalidRows = 0

try {
    if (Test-Path $LogRoot) {
        $logFiles = @(Get-ChildItem -Path $LogRoot -Filter "*.log" -Recurse -File -ErrorAction SilentlyContinue)
    } else {
        Add-Error "IIS log root does not exist: $LogRoot"
    }

    foreach ($file in $logFiles) {
        $fields = @()
        foreach ($line in Get-Content -LiteralPath $file.FullName -ErrorAction SilentlyContinue) {
            $trimmedLine = $line.Trim()
            if ([string]::IsNullOrWhiteSpace($trimmedLine)) {
                continue
            }
            if ($trimmedLine.StartsWith("#Fields:")) {
                $fields = $trimmedLine.Substring(8).Trim().Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
                $filesWithFields += 1
                if (-not ($fields -contains "cs-uri-stem")) {
                    $filesMissingUriField += 1
                    Add-Error "Missing required W3C field cs-uri-stem in $($file.FullName)"
                }
                continue
            }
            if ($trimmedLine.StartsWith("#")) {
                continue
            }
            if ($fields.Count -eq 0) {
                $invalidRows += 1
                continue
            }

            $values = $trimmedLine.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
            $map = @{}
            for ($index = 0; $index -lt $fields.Count; $index++) {
                $value = if ($index -lt $values.Count) { $values[$index] } else { "-" }
                $map[$fields[$index]] = $value
            }

            $uri = Get-FieldValue $map "cs-uri-stem"
            if ($uri -eq "-" -or [string]::IsNullOrWhiteSpace($uri)) {
                $invalidRows += 1
                continue
            }
            if (-not ($uri -match "^/api(/|$)")) {
                continue
            }

            $date = Get-FieldValue $map "date"
            $time = Get-FieldValue $map "time"
            $timestamp = if ($date -ne "-" -and $time -ne "-") { "$date`T$time`Z" } else { "UNKNOWN" }
            $client = Get-FieldValue $map "c-ip"
            $statusCode = Get-FieldValue $map "sc-status"
            $userAgent = Get-FieldValue $map "cs(User-Agent)"

            $rows += New-EvidenceRow `
                -Timestamp $timestamp `
                -Source $file.FullName `
                -Client $client `
                -Endpoint $uri `
                -StatusCode $statusCode `
                -UserAgent $userAgent
        }
    }

    Ensure-OutputFile -Path $OutputPath -Rows $rows
    $legacyCount = @($rows | Where-Object { $_.endpoint -like "/api/*" -and $_.endpoint -notlike "/api/v1/*" }).Count
    $djangoCount = @($rows | Where-Object { $_.endpoint -like "/api/v1/*" }).Count

    @{
        status = if ($rows.Count -gt 0) { "IIS_EVIDENCE_EXPORTED" } else { "IIS_EVIDENCE_INCOMPLETE" }
        log_root = $LogRoot
        log_files_checked = $logFiles.Count
        files_with_w3c_fields = $filesWithFields
        files_missing_uri_field = $filesMissingUriField
        invalid_rows = $invalidRows
        rows_exported = $rows.Count
        legacy_rows = $legacyCount
        django_rows = $djangoCount
        output = $OutputPath
        errors = $errors
    } | ConvertTo-Json -Depth 6
    exit 0
} catch {
    Ensure-OutputFile -Path $OutputPath -Rows @()
    @{
        status = "IIS_EVIDENCE_INCOMPLETE"
        log_root = $LogRoot
        log_files_checked = $logFiles.Count
        files_with_w3c_fields = $filesWithFields
        files_missing_uri_field = $filesMissingUriField
        invalid_rows = $invalidRows
        rows_exported = 0
        legacy_rows = 0
        django_rows = 0
        output = $OutputPath
        errors = @($_.Exception.Message)
    } | ConvertTo-Json -Depth 6
    exit 0
}
