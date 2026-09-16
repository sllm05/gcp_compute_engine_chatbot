# Google Cloud Run 2 (ADC / Agent Platform) 로컬 서버
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Google Cloud Run 2 (ADC / Agent Platform) 로컬 서버" -ForegroundColor Cyan
Write-Host "  인증 방식: ADC (Application Default Credentials - Keyless)" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan

$pythonExe = "C:\Users\KIM DONGJUN\miniconda3\envs\myenv\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$env:PORT = "8080"
$env:GOOGLE_CLOUD_PROJECT = "iceu-songpa09"
$env:GOOGLE_CLOUD_LOCATION = "us-central1"

Write-Host "[정보] 서버 접속 주소: http://localhost:8080" -ForegroundColor Green
& $pythonExe -m uvicorn app:app --host 0.0.0.0 --port 8080 --reload
