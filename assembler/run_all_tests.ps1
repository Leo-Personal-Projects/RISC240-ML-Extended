$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Running MLASM built-in self-test..."
python .\MLASM.py --self-test
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Running all assembly/simulator tests..."
python .\verify_all_tests.py
exit $LASTEXITCODE
