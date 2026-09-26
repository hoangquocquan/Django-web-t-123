Set-StrictMode -Version Latest

function New-N8nCliDescriptor {
    param(
        [Parameter(Mandatory = $true)][string]$Candidate,
        [Parameter(Mandatory = $true)][string]$Source
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
        [AllowNull()][string]$OverridePath
    )

    if (-not [string]::IsNullOrWhiteSpace($OverridePath)) {
        if (-not (Test-Path -LiteralPath $OverridePath -PathType Leaf)) {
            throw "N8N CLI NOT FOUND"
        }
        return New-N8nCliDescriptor -Candidate $OverridePath -Source "override"
    }

    foreach ($commandName in @("n8n", "n8n.cmd")) {
        $command = Get-Command $commandName -CommandType Application, ExternalScript `
            -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($command -and (Test-Path -LiteralPath $command.Source -PathType Leaf)) {
            return New-N8nCliDescriptor -Candidate $command.Source -Source "path"
        }
    }

    $localBin = Join-Path $Repo "node_modules\.bin"
    foreach ($candidate in @(
        (Join-Path $localBin "n8n.cmd"),
        (Join-Path $localBin "n8n.ps1"),
        (Join-Path $Repo "node_modules\n8n\bin\n8n")
    )) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return New-N8nCliDescriptor -Candidate $candidate -Source "project-local"
        }
    }

    $npm = Get-Command npm.cmd, npm -CommandType Application, ExternalScript `
        -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($npm) {
        $npmRootOutput = @(& $npm.Source root -g 2>$null)
        if ($LASTEXITCODE -eq 0 -and $npmRootOutput.Count -gt 0) {
            $npmRoot = [string]$npmRootOutput[-1]
            $npmBinRoot = Split-Path -Parent $npmRoot
            foreach ($candidate in @(
                (Join-Path $npmBinRoot "n8n.cmd"),
                (Join-Path $npmBinRoot "n8n.ps1"),
                (Join-Path $npmRoot "n8n\bin\n8n")
            )) {
                if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                    return New-N8nCliDescriptor -Candidate $candidate -Source "npm-global-root"
                }
            }
        }
    }

    throw "N8N CLI NOT FOUND"
}

Export-ModuleMember -Function Resolve-N8nCli
