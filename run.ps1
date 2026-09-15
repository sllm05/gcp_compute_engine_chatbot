# Google Gemini 3.8 / 3.7 Flash 챗봇 서버 실행 스크립트
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Google Gemini 3.8 / 3.7 Flash 챗봇 서버 시작" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

$pythonExe = "C:\Users\KIM DONGJUN\miniconda3\envs\myenv\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "[정보] 서버 접속 주소: http://localhost:8000" -ForegroundColor Green
& $pythonExe -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
