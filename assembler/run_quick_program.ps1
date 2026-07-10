$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python .\MLASM.py .\quick_program.asm
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python .\MLSIM.py .\quick_program.hex --run --trace
