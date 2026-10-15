$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
python -m scripts.validate_v2
if ($LASTEXITCODE -ne 0) { throw 'Core validation failed. Inspect runtime/verification-v2.' }
