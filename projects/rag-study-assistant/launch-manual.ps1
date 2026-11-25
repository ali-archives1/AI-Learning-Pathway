$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$manualPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $manualPython)) {
    throw 'First create .venv and install requirements.txt using the README setup steps.'
}
& $manualPython (Join-Path $PSScriptRoot 'src\manual_app.py')
