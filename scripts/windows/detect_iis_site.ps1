param(
    [string]$DefaultLogRoot = "C:\inetpub\logs\LogFiles"
)

$ErrorActionPreference = "Stop"

function Write-JsonResult {
    param([hashtable]$Result)
    $Result | ConvertTo-Json -Depth 8
}

try {
    if (-not (Get-Command Get-Website -ErrorAction SilentlyContinue)) {
        try {
            Import-Module WebAdministration -ErrorAction Stop
        } catch {
            Write-JsonResult @{
                status = "IIS_SITE_DETECTION_UNAVAILABLE"
                websites = @()
                default_log_root = $DefaultLogRoot
                errors = @("IIS WebAdministration module is not available.")
            }
            exit 0
        }
    }

    $websites = @(Get-Website | ForEach-Object {
        $siteId = [string]$_.id
        [pscustomobject]@{
            website_name = $_.name
            site_id = $siteId
            physical_path = $_.physicalPath
            log_location = (Join-Path $DefaultLogRoot ("W3SVC{0}" -f $siteId))
        }
    })

    Write-JsonResult @{
        status = if ($websites.Count -gt 0) { "IIS_SITES_DETECTED" } else { "IIS_NO_SITES_DETECTED" }
        websites = $websites
        default_log_root = $DefaultLogRoot
        errors = @()
    }
    exit 0
} catch {
    Write-JsonResult @{
        status = "IIS_SITE_DETECTION_FAILED"
        websites = @()
        default_log_root = $DefaultLogRoot
        errors = @($_.Exception.Message)
    }
    exit 0
}
