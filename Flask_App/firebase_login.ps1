# PhishGuard AI - Firebase email/password login for local API testing
# IMPORTANT: Dot-source this script so the token remains available in your current shell:
# . .\firebase_login.ps1

$ErrorActionPreference = "Stop"

$ApiKey = Read-Host "Firebase Web API Key"
$Email = Read-Host "Firebase test-user email"
$SecurePassword = Read-Host "Firebase test-user password" -AsSecureString
$Bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword)

try {
    $PlainPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Bstr)

    $RequestBody = @{
        email             = $Email
        password          = $PlainPassword
        returnSecureToken = $true
    } | ConvertTo-Json

    $AuthResponse = Invoke-RestMethod `
        -Uri "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=$ApiKey" `
        -Method Post `
        -ContentType "application/json" `
        -Body $RequestBody

    # Token stays in this PowerShell session; it is never saved to disk.
    $PhishGuardIdToken = $AuthResponse.idToken
    $PhishGuardAuthHeaders = @{
        Authorization = "Bearer $PhishGuardIdToken"
    }

    Write-Host "`nFirebase login successful." -ForegroundColor Green
    Write-Host "Token stored in `$PhishGuardIdToken for this PowerShell session."
    Write-Host "Headers stored in `$PhishGuardAuthHeaders."
    Write-Host "Token expires in approximately $($AuthResponse.expiresIn) seconds."
    Write-Host "`nExample protected API request:" -ForegroundColor Cyan
    Write-Host '$body = @{ url = "https://example.com" } | ConvertTo-Json'
    Write-Host 'Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/scan" -Method Post -Headers $PhishGuardAuthHeaders -ContentType "application/json" -Body $body'
}
catch {
    $PhishGuardIdToken = $null
    $PhishGuardAuthHeaders = $null
    Write-Error "Firebase login failed. Check the Web API key, test-user email/password, and Email/Password sign-in setting. Details: $($_.Exception.Message)"
}
finally {
    if ($Bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Bstr)
    }
    $PlainPassword = $null
    $RequestBody = $null
    $SecurePassword = $null
}