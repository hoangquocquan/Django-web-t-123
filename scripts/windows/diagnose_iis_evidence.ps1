param(
    [string]$LogRoot = "C:\inetpub\logs\LogFiles",
    [int]$SampleLimit = 10
)

$ErrorActionPreference = "Stop"

function Get-W3CFields {
    param([string]$Path)
    foreach ($line in Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue) {
        $trimmedLine = $line.Trim()
        if ($trimmedLine.StartsWith("#Fields:")) {
            return $trimmedLine.Substring(8).Trim().Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
        }
    }
    return @()
}

function Get-ApiRows {
    param([string]$Path, [string[]]$Fields)

    $rows = @()
    if ($Fields.Count -eq 0) {
        return $rows
    }

    foreach ($line in Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue) {
        $trimmedLine = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmedLine) -or $trimmedLine.StartsWith("#")) {
            continue
        }

        $values = $trimmedLine.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
        $map = @{}
        for ($index = 0; $index -lt $Fields.Count; $index++) {
            $map[$Fields[$index]] = if ($index -lt $values.Count) { $values[$index] } else { "-" }
        }

        $uri = if ($map.ContainsKey("cs-uri-stem")) { $map["cs-uri-stem"] } else { "-" }
        if ($uri -match "^/api(/|$)") {
            $rows += [pscustomobject]@{
                source = $Path
                endpoint = $uri
                client = if ($map.ContainsKey("c-ip")) { $map["c-ip"] } else { "-" }
                status_code = if ($map.ContainsKey("sc-status")) { $map["sc-status"] } else { "-" }
                user_agent = if ($map.ContainsKey("cs(User-Agent)")) { $map["cs(User-Agent)"] } else { "-" }
            }
        }
    }
    return $rows
}

$errors = @()
$logFiles = @()
$fieldReports = @()
$apiRows = @()

if (Test-Path $LogRoot) {
    $logFiles = @(Get-ChildItem -Path $LogRoot -Filter "*.log" -Recurse -File -ErrorAction SilentlyContinue)
} else {
    $errors += "IIS log path does not exist: $LogRoot"
}

foreach ($file in $logFiles) {
    $fields = @(Get-W3CFields -Path $file.FullName)
    $rows = @(Get-ApiRows -Path $file.FullName -Fields $fields)
    $apiRows += $rows
    $fieldReports += [pscustomobject]@{
        file = $file.FullName
        fields = $fields
        has_date = $fields -contains "date"
        has_time = $fields -contains "time"
        has_client_ip = $fields -contains "c-ip"
        has_uri_stem = $fields -contains "cs-uri-stem"
        has_status = $fields -contains "sc-status"
        has_user_agent = $fields -contains "cs(User-Agent)"
        api_rows = $rows.Count
    }
}

$legacyCount = @($apiRows | Where-Object { $_.endpoint -match "^/api/" -and $_.endpoint -notmatch "^/api/v1(/|$)" }).Count
$djangoCount = @($apiRows | Where-Object { $_.endpoint -match "^/api/v1(/|$)" }).Count

@{
    status = if ($apiRows.Count -gt 0) { "IIS_DIAGNOSTIC_HAS_API_TRAFFIC" } else { "IIS_DIAGNOSTIC_NO_API_TRAFFIC" }
    log_path = $LogRoot
    available_log_files = $logFiles.Count
    detected_w3c_fields = $fieldReports
    sample_api_requests = @($apiRows | Select-Object -First $SampleLimit)
    api_request_counts = @{
        total = $apiRows.Count
        legacy_api = $legacyCount
        django_api_v1 = $djangoCount
    }
    errors = $errors
    safety = @{
        iis_modified = $false
        routes_changed = $false
        shutdown_executed = $false
    }
} | ConvertTo-Json -Depth 8
