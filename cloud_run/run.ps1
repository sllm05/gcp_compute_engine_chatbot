# Google Cloud Run 로컬 테스트 서버 (포트 8080)
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Google Cloud Run 로컬 테스트 서버 (포트 8080)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

$pythonExe = "C:\Users\KIM DONGJUN\miniconda3\envs\myenv\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$env:PORT = "8080"
Write-Host "[정보] 서버 접속 주소: http://localhost:8080" -ForegroundColor Green
& $pythonExe -m uvicorn app:app --host 0.0.0.0 --port 8080 --reload
