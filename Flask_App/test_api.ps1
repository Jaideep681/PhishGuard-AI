$body = @{ url = "https://example.com" } | ConvertTo-Json

$result = Invoke-RestMethod `
  -Uri "http://127.0.0.1:5000/api/scan" `
  -Method Post `
  -Headers $PhishGuardAuthHeaders `
  -ContentType "application/json" `
  -Body $body

$result | ConvertTo-Json -Depth 10