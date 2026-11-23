
# PhishGuard AI - QR Scan Test (PowerShell 7)

$ErrorActionPreference = "Stop"

# Check authentication
if (-not $PhishGuardAuthHeaders -or
    -not $PhishGuardAuthHeaders.Authorization) {

    Write-Host "Firebase login required." -ForegroundColor Yellow
    Write-Host "Run: . .\firebase_login.ps1"
    return
}

# Select image
$imagePath = Read-Host "Enter the full path of a QR image"

if (-not (Test-Path -LiteralPath $imagePath -PathType Leaf)) {
    throw "Image file not found: $imagePath"
}

# Upload image
$form = @{
    file = Get-Item -LiteralPath $imagePath
}

try {
    $result = Invoke-RestMethod `
        -Uri "http://127.0.0.1:5000/api/qr-scan" `
        -Method Post `
        -Headers $PhishGuardAuthHeaders `
        -Form $form

    Write-Host "`nQR Scan Result:" -ForegroundColor Green
    $result | ConvertTo-Json -Depth 10
}
catch {
    Write-Host "`nQR scan failed:" -ForegroundColor Red

    if ($_.ErrorDetails.Message) {
        Write-Host $_.ErrorDetails.Message
    } else {
        Write-Host $_.Exception.Message
    }
}
