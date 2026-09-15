param([int]$Port = 8765)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Missing .venv. Follow README installation steps first.'
}
Set-Location -LiteralPath $projectRoot
$env:PYTHONUTF8 = '1'
& $pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port $Port
exit $LASTEXITCODE

