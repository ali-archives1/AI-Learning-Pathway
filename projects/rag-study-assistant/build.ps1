param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
$ProjectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectDirectory

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Python environment not found at '$PythonExe'. Create it and install requirements.txt first."
}

& $PythonExe -m PyInstaller --clean --noconfirm .\RAGStudyAssistant.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

Write-Host "Build complete: $ProjectDirectory\dist\RAG Study Assistant.exe"
