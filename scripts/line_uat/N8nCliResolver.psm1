Set-StrictMode -Version Latest

function New-N8nCliDescriptor {
    param(
        [Parameter(Mandatory = $true)][string]$Candidate,
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$ExpectedVersion
    )

    $resolved = (Resolve-Path -LiteralPath $Candidate -ErrorAction Stop).Path
    $extension = [IO.Path]::GetExtension($resolved).ToLowerInvariant()

    if ($extension -eq ".ps1") {
        $cmdSibling = [IO.Path]::ChangeExtension($resolved, ".cmd")
        if (Test-Path -LiteralPath $cmdSibling -PathType Leaf) {
            $resolved = (Resolve-Path -LiteralPath $cmdSibling).Path
            $extension = ".cmd"
        }
    }

    $filePath = $resolved
    $prefixArguments = @()
    if ($extension -eq ".ps1") {
        $powerShell = (Get-Command powershell.exe -CommandType Application -ErrorAction Stop).Source
        $filePath = $powerShell
        $prefixArguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $resolved)
    }
    elseif ($extension -notin @(".cmd", ".bat", ".exe", ".com")) {
        $node = Get-Command node.exe, node -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if (-not $node) { throw "N8N CLI NOT FOUND" }
        $filePath = $node.Source
        $prefixArguments = @($resolved)
    }

    $versionOutput = @(& $filePath @prefixArguments --version 2>$null)
    if ($LASTEXITCODE -ne 0) { throw "N8N CLI NOT FOUND" }
    $versionMatch = [regex]::Match(($versionOutput -join " "), '\b\d+\.\d+\.\d+\b')
    if (-not $versionMatch.Success) { throw "N8N CLI NOT FOUND" }
    if ($versionMatch.Value -ne $ExpectedVersion) { throw "N8N VERSION MISMATCH" }

    return [pscustomobject]@{
        FilePath = $filePath
        PrefixArguments = [string[]]$prefixArguments
        ResolvedPath = $resolved
        Source = $Source
        Version = $versionMatch.Value
    }
}

function Resolve-N8nCli {
    param(
        [Parameter(Mandatory = $true)][string]$Repo,
        [AllowNull()][string]$ProcessOverridePath,
        [AllowNull()][string]$UserOverridePath,
        [Parameter(Mandatory = $true)][string]$ExpectedVersion
    )

    foreach ($override in @(
        [pscustomobject]@{ Path = $ProcessOverridePath; Source = "process-override" },
        [pscustomobject]@{ Path = $UserOverridePath; Source = "user-override" }
    )) {
        if (-not [string]::IsNullOrWhiteSpace($override.Path)) {
            if (-not (Test-Path -LiteralPath $override.Path -PathType Leaf)) {
                throw "N8N CLI NOT FOUND"
            }
            return New-N8nCliDescriptor -Candidate $override.Path `
                -Source $override.Source -ExpectedVersion $ExpectedVersion
        }
    }

    $candidates = [Collections.Generic.List[object]]::new()
    $seen = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )

    function Add-N8nCandidate {
        param([AllowNull()][string]$Path, [string]$Source)
        if ([string]::IsNullOrWhiteSpace($Path)) { return }
        if ($seen.Add($Path)) {
            [void]$candidates.Add([pscustomobject]@{ Path = $Path; Source = $Source })
        }
    }

    foreach ($commandName in @("n8n", "n8n.cmd")) {
        $commands = @(Get-Command $commandName -All `
            -CommandType Application, ExternalScript -ErrorAction SilentlyContinue)
        foreach ($command in $commands) {
            Add-N8nCandidate -Path $command.Source -Source "path"
        }
    }

    $localBin = Join-Path $Repo "node_modules\.bin"
    Add-N8nCandidate -Path (Join-Path $localBin "n8n.cmd") -Source "project-local"
    Add-N8nCandidate -Path (Join-Path $localBin "n8n.ps1") -Source "project-local"
    Add-N8nCandidate -Path (Join-Path $Repo "node_modules\n8n\bin\n8n") `
        -Source "project-local"

    $npmCommands = @(Get-Command npm.cmd, npm -All `
        -CommandType Application, ExternalScript -ErrorAction SilentlyContinue)
    foreach ($npm in $npmCommands) {
        $prefixOutput = @(& $npm.Source config get prefix 2>$null)
        if ($LASTEXITCODE -eq 0 -and $prefixOutput.Count -gt 0) {
            $prefix = [string]$prefixOutput[-1]
            Add-N8nCandidate -Path (Join-Path $prefix "n8n.cmd") -Source "npm-prefix"
            Add-N8nCandidate -Path (Join-Path $prefix "n8n.ps1") -Source "npm-prefix"
            Add-N8nCandidate -Path (Join-Path $prefix "node_modules\n8n\bin\n8n") `
                -Source "npm-prefix"
        }

        $rootOutput = @(& $npm.Source root -g 2>$null)
        if ($LASTEXITCODE -eq 0 -and $rootOutput.Count -gt 0) {
            $npmRoot = [string]$rootOutput[-1]
            $npmBinRoot = Split-Path -Parent $npmRoot
            Add-N8nCandidate -Path (Join-Path $npmBinRoot "n8n.cmd") `
                -Source "npm-global-root"
            Add-N8nCandidate -Path (Join-Path $npmBinRoot "n8n.ps1") `
                -Source "npm-global-root"
            Add-N8nCandidate -Path (Join-Path $npmRoot "n8n\bin\n8n") `
                -Source "npm-global-root"
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($env:NVM_SYMLINK)) {
        Add-N8nCandidate -Path (Join-Path $env:NVM_SYMLINK "n8n.cmd") `
            -Source "nvm-symlink"
        Add-N8nCandidate -Path (Join-Path $env:NVM_SYMLINK "n8n.ps1") `
            -Source "nvm-symlink"
    }

    foreach ($pathEntry in @($env:PATH -split ';')) {
        if (-not [string]::IsNullOrWhiteSpace($pathEntry)) {
            Add-N8nCandidate -Path (Join-Path $pathEntry "n8n.cmd") `
                -Source "active-path"
            Add-N8nCandidate -Path (Join-Path $pathEntry "n8n.ps1") `
                -Source "active-path"
        }
    }

    $versionMismatch = $false
    foreach ($candidate in $candidates) {
        if (-not (Test-Path -LiteralPath $candidate.Path -PathType Leaf)) { continue }
        try {
            return New-N8nCliDescriptor -Candidate $candidate.Path `
                -Source $candidate.Source -ExpectedVersion $ExpectedVersion
        }
        catch {
            if ($_.Exception.Message -eq "N8N VERSION MISMATCH") {
                $versionMismatch = $true
            }
        }
    }

    if ($versionMismatch) { throw "N8N VERSION MISMATCH" }
    throw "N8N CLI NOT FOUND"
}

Export-ModuleMember -Function Resolve-N8nCli
