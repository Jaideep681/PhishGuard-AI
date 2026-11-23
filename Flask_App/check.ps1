$result = Invoke-RestMethod `
    -Uri "http://127.0.0.1:5000/api/scan" `
    -Method Post `
    -Headers $PhishGuardAuthHeaders `
    -ContentType "application/json" `
    -Body '{"url":"https://www.rag.com"}'

$result.data | Format-List