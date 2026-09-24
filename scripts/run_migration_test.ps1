param(
    [string]$DjangoBackendPath = "django_backend"
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "== $Name =="
    & $Command

    if ($LASTEXITCODE -ne 0) {
        Write-Host "MIGRATION TEST FAILED: $Name"
        exit $LASTEXITCODE
    }
}

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path $ProjectRoot $DjangoBackendPath

Push-Location $BackendPath
try {
    Invoke-Step "Step 1: Django system check" {
        python manage.py check
    }
}
finally {
    Pop-Location
}

Invoke-Step "Step 2: Catalog module tests" {
    pytest django_backend/apps/catalog/tests
}

Invoke-Step "Step 3: CRM module tests" {
    pytest django_backend/apps/crm/tests
}

Invoke-Step "Step 4: Sales module tests" {
    pytest django_backend/apps/sales/tests
}

Invoke-Step "Step 5: CMS module tests" {
    pytest django_backend/apps/cms/tests
}

Invoke-Step "Step 6: Auth module tests" {
    pytest django_backend/apps/accounts/tests
}

Push-Location $BackendPath
try {
    Invoke-Step "Step 7: Full regression tests" {
        pytest
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "MIGRATION TEST PASSED"
