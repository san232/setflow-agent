$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$env:PYTHONUTF8 = '1'
& '.\.venv\Scripts\python.exe' -m pytest -q
exit $LASTEXITCODE

