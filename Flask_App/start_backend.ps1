# PhishGuard AI - Start Flask backend
# Run this script from any PowerShell location.
$ErrorActionPreference = "Stop"

$FlaskAppDir = $PSScriptRoot
$VenvActivate = Join-Path $FlaskAppDir "venv\Scripts\Activate.ps1"
$AppFile = Join-Path $FlaskAppDir "app.py"

if (-not (Test-Path $VenvActivate)) {
    throw "Virtual environment not found: $VenvActivate"
}
if (-not (Test-Path $AppFile)) {
    throw "Flask app not found: $AppFile"
}

Set-Location $FlaskAppDir
. $VenvActivate

Write-Host "`nStarting PhishGuard AI backend..." -ForegroundColor Cyan
Write-Host "Health check: http://127.0.0.1:5000/api/health`n" -ForegroundColor Green

python $AppFile