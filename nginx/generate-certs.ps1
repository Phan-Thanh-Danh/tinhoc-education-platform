# PowerShell Script: Tạo chứng chỉ SSL Self-signed cho Localhost HTTPS
param(
    [string]$Domain = "localhost",
    [int]$Days = 365
)

$certsDir = Join-Path $PSScriptRoot "certs"
if (-not (Test-Path $certsDir)) {
    New-Item -ItemType Directory -Path $certsDir -Force | Out-Null
}

$keyFile = Join-Path $certsDir "key.pem"
$certFile = Join-Path $certsDir "cert.pem"

Write-Host "Đang tạo chứng chỉ SSL cho: $Domain ..." -ForegroundColor Cyan

$opensslPaths = @(
    "openssl",
    "C:\Program Files\Git\usr\bin\openssl.exe",
    "C:\Program Files\OpenSSL-Win64\bin\openssl.exe"
)

$opensslCmd = $null
foreach ($path in $opensslPaths) {
    if (Get-Command $path -ErrorAction SilentlyContinue) {
        $opensslCmd = $path
        break
    }
}

if (-not $opensslCmd) {
    Write-Error "Không tìm thấy OpenSSL. Vui lòng cài đặt OpenSSL hoặc Git for Windows."
    exit 1
}

& $opensslCmd req -x509 -nodes -days $Days -newkey rsa:2048 `
    -keyout $keyFile -out $certFile `
    -subj "/C=VN/ST=HCM/L=HCM/O=TinHocEducation/CN=$Domain" `
    -addext "subjectAltName=DNS:$Domain,IP:127.0.0.1"

Write-Host "Tạo chứng chỉ SSL thành công!" -ForegroundColor Green
Write-Host "Cert: $certFile"
Write-Host "Key:  $keyFile"
