param(
    [int]$Days = 7,
    [string]$Environment = "production",
    [string]$SiteName = "",
    [string]$SiteId = "",
    [string]$LogRoot = "",
    [string]$PackageRoot = "docs\migration\production_evidence",
    [string]$Operator = $env:USERNAME,
    [string]$Reviewer = "PENDING",
    [string]$PythonCommand = "python"
)

$ErrorActionPreference = "Stop"

function New-StepResult {
    param(
        [string]$Name,
        [string]$Status,
        [object]$Data,
        [string[]]$Errors = @()
    )

    return [pscustomobject]@{
        name = $Name
        status = $Status
        data = $Data
        errors = $Errors
    }
}

function Test-IISInstalled {
    if (Get-Command Get-Website -ErrorAction SilentlyContinue) {
        return $true
    }

    try {
        Import-Module WebAdministration -ErrorAction Stop
        return [bool](Get-Command Get-Website -ErrorAction SilentlyContinue)
    } catch {
        return $false
    }
}

function Get-IISWebsitesSafe {
    if (-not (Test-IISInstalled)) {
        return @()
    }

    try {
        return @(Get-Website | ForEach-Object {
            [pscustomobject]@{
                site_name = $_.Name
                site_id = [string]$_.Id
                physical_path = $_.PhysicalPath
            }
        })
    } catch {
        return @()
    }
}

function Select-IISWebsite {
    param([object[]]$Websites)

    if ($Websites.Count -eq 0) {
        return $null
    }
    if (-not [string]::IsNullOrWhiteSpace($SiteId)) {
        $match = $Websites | Where-Object { $_.site_id -eq $SiteId } | Select-Object -First 1
        if ($match) {
            return $match
        }
    }
    if (-not [string]::IsNullOrWhiteSpace($SiteName)) {
        $match = $Websites | Where-Object { $_.site_name -eq $SiteName } | Select-Object -First 1
        if ($match) {
            return $match
        }
    }
    return $Websites | Select-Object -First 1
}

function Resolve-LogRoot {
    param([object]$SelectedSite)

    if (-not [string]::IsNullOrWhiteSpace($LogRoot)) {
        return $LogRoot
    }
    if ($SelectedSite -and -not [string]::IsNullOrWhiteSpace($SelectedSite.site_id)) {
        return "C:\inetpub\logs\LogFiles\W3SVC$($SelectedSite.site_id)"
    }
    return "C:\inetpub\logs\LogFiles"
}

function Get-W3CFields {
    param([string]$Path)

    foreach ($line in Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue) {
        $trimmed = $line.Trim()
        if ($trimmed.StartsWith("#Fields:")) {
            return $trimmed.Substring(8).Trim().Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
        }
    }
    return @()
}

function Get-RecentLogFiles {
    param([string]$Root, [int]$WindowDays)

    if (-not (Test-Path -LiteralPath $Root)) {
        return @()
    }

    $cutoff = (Get-Date).AddDays(-1 * [Math]::Max(1, $WindowDays))
    return @(Get-ChildItem -LiteralPath $Root -Filter "u_ex*.log" -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -ge $cutoff } |
        Sort-Object LastWriteTime)
}

function Initialize-Package {
    param([string]$Root)

    $inputDir = Join-Path $Root "input"
    $logDir = Join-Path $inputDir "iis_logs"
    $reportDir = Join-Path $Root "reports"
    $handoverDir = Join-Path $Root "handover"

    foreach ($directory in @($inputDir, $logDir, $reportDir, $handoverDir)) {
        if (-not (Test-Path -LiteralPath $directory)) {
            New-Item -ItemType Directory -Force -Path $directory | Out-Null
        }
    }

    return [pscustomobject]@{
        root = $Root
        input_dir = $inputDir
        iis_log_dir = $logDir
        report_dir = $reportDir
        handover_dir = $handoverDir
        csv_path = Join-Path $inputDir "iis_api_evidence.csv"
        metadata_path = Join-Path $handoverDir "collection_metadata.json"
    }
}

function Copy-RecentLogs {
    param([object[]]$LogFiles, [string]$Destination)

    $copied = @()
    foreach ($file in $LogFiles) {
        $target = Join-Path $Destination $file.Name
        Copy-Item -LiteralPath $file.FullName -Destination $target -Force
        $copied += $target
    }
    return $copied
}

function Test-W3CLogging {
    param([object[]]$LogFiles)

    $requiredFields = @("date", "time", "c-ip", "cs-uri-stem", "sc-status", "cs(User-Agent)")
    $reports = @()
    $errors = @()

    foreach ($file in $LogFiles) {
        $fields = @(Get-W3CFields -Path $file.FullName)
        $missing = @($requiredFields | Where-Object { $fields -notcontains $_ })
        if ($missing.Count -gt 0) {
            $errors += "Missing W3C fields in $($file.FullName): $($missing -join ', ')"
        }
        $reports += [pscustomobject]@{
            file = $file.FullName
            fields = $fields
            missing_fields = $missing
        }
    }

    return [pscustomobject]@{
        status = if ($errors.Count -eq 0 -and $LogFiles.Count -gt 0) { "W3C_LOGGING_VALID" } else { "W3C_LOGGING_INVALID" }
        reports = $reports
        errors = $errors
    }
}

function Write-Metadata {
    param(
        [string]$Path,
        [object]$SelectedSite,
        [string]$ResolvedLogRoot,
        [int]$WindowDays
    )

    $end = Get-Date
    $start = $end.AddDays(-1 * [Math]::Max(1, $WindowDays))
    $metadata = [ordered]@{
        server = $env:COMPUTERNAME
        environment = $Environment
        iis_site = if ($SelectedSite) { $SelectedSite.site_name } elseif (-not [string]::IsNullOrWhiteSpace($SiteName)) { $SiteName } else { "PENDING" }
        site_id = if ($SelectedSite) { $SelectedSite.site_id } elseif (-not [string]::IsNullOrWhiteSpace($SiteId)) { $SiteId } else { "PENDING" }
        collection_start = $start.ToString("yyyy-MM-dd")
        collection_end = $end.ToString("yyyy-MM-dd")
        operator = if ([string]::IsNullOrWhiteSpace($Operator)) { "PENDING" } else { $Operator }
        reviewer = if ([string]::IsNullOrWhiteSpace($Reviewer)) { "PENDING" } else { $Reviewer }
        notes = "Automated IIS production evidence collection. LogRoot=$ResolvedLogRoot; Days=$WindowDays."
    }
    $metadata | ConvertTo-Json -Depth 6 | Set-Content -Path $Path -Encoding UTF8
    return $metadata
}

function Invoke-JsonCommand {
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
        return New-StepResult -Name $Name -Status "STEP_COMPLETED" -Data $parsed
    } catch {
        return New-StepResult -Name $Name -Status "STEP_FAILED" -Data $null -Errors @($_.Exception.Message)
    }
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptRoot "..\..")
$exportScript = Join-Path $scriptRoot "export_iis_api_evidence.ps1"
$acceptanceValidator = Join-Path $projectRoot "scripts\phase11_1_6_5_2_evidence_acceptance_validator.py"
$package = Initialize-Package -Root $PackageRoot
$steps = @()
$errors = @()

$iisInstalled = Test-IISInstalled
$websites = @(Get-IISWebsitesSafe)
$selectedSite = Select-IISWebsite -Websites $websites
$resolvedLogRoot = Resolve-LogRoot -SelectedSite $selectedSite
$logFiles = @(Get-RecentLogFiles -Root $resolvedLogRoot -WindowDays $Days)
$w3cValidation = Test-W3CLogging -LogFiles $logFiles
$copiedLogs = Copy-RecentLogs -LogFiles $logFiles -Destination $package.iis_log_dir
$metadata = Write-Metadata -Path $package.metadata_path -SelectedSite $selectedSite -ResolvedLogRoot $resolvedLogRoot -WindowDays $Days

if (-not $iisInstalled) {
    $errors += "IIS is not installed or WebAdministration module is unavailable."
}
if ($websites.Count -eq 0) {
    $errors += "No IIS websites were detected."
}
if (-not (Test-Path -LiteralPath $resolvedLogRoot)) {
    $errors += "IIS log root does not exist: $resolvedLogRoot"
}
if ($logFiles.Count -eq 0) {
    $errors += "No IIS log files were found in the selected collection window."
}
$errors += $w3cValidation.errors

$steps += New-StepResult -Name "detect_iis_installation" -Status ($(if ($iisInstalled) { "IIS_DETECTED" } else { "IIS_NOT_DETECTED" })) -Data @{ installed = $iisInstalled }
$steps += New-StepResult -Name "detect_iis_websites" -Status ($(if ($websites.Count -gt 0) { "IIS_WEBSITES_DETECTED" } else { "IIS_NO_WEBSITES_DETECTED" })) -Data @{ websites = $websites; selected_site = $selectedSite }
$steps += New-StepResult -Name "locate_iis_logs" -Status ($(if (Test-Path -LiteralPath $resolvedLogRoot) { "IIS_LOG_ROOT_FOUND" } else { "IIS_LOG_ROOT_MISSING" })) -Data @{ log_root = $resolvedLogRoot; files_found = $logFiles.Count }
$steps += New-StepResult -Name "validate_w3c_logging" -Status $w3cValidation.status -Data $w3cValidation
$steps += New-StepResult -Name "collect_logs" -Status ($(if ($copiedLogs.Count -gt 0) { "IIS_LOGS_COLLECTED" } else { "IIS_LOGS_NOT_COLLECTED" })) -Data @{ copied_logs = $copiedLogs; days = $Days }
$steps += New-StepResult -Name "generate_metadata" -Status "METADATA_GENERATED" -Data @{ path = $package.metadata_path; metadata = $metadata }

$steps += Invoke-JsonCommand -Name "export_iis_api_evidence" -Command {
    powershell -ExecutionPolicy Bypass -File $exportScript -LogRoot $package.iis_log_dir -OutputPath $package.csv_path
}

$steps += Invoke-JsonCommand -Name "run_acceptance_validator" -Command {
    & $PythonCommand $acceptanceValidator --package-dir $package.root
}

$validatorStep = $steps | Where-Object { $_.name -eq "run_acceptance_validator" } | Select-Object -First 1
$validatorStatus = if ($validatorStep -and $validatorStep.data -and $validatorStep.data.status) {
    $validatorStep.data.status
} else {
    "EVIDENCE_REJECTED"
}

@{
    status = if ($validatorStatus -eq "EVIDENCE_ACCEPTED") { "COMPLETE_EVIDENCE_PACKAGE" } else { "INCOMPLETE_EVIDENCE_PACKAGE" }
    iis_installed = $iisInstalled
    websites = $websites
    selected_site = $selectedSite
    log_root = $resolvedLogRoot
    days = $Days
    evidence_package = $package.root
    csv_path = $package.csv_path
    metadata_path = $package.metadata_path
    copied_logs = $copiedLogs
    validator_status = $validatorStatus
    steps = $steps
    errors = $errors
    safety = @{
        shutdown_executed = $false
        legacy_api_disabled = $false
        iis_modified = $false
        proxy_modified = $false
        routes_changed = $false
        database_modified = $false
    }
} | ConvertTo-Json -Depth 14
