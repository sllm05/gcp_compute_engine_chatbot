# Google Gemini 3.8 / 3.7 Flash 챗봇 서버 실행 스크립트 (루트 진입점)
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Google Gemini 3.8 / 3.7 Flash 챗봇 서버 시작" -ForegroundColor Cyan
Write-Host "  (위치: compute_engine 서브폴더)" -ForegroundColor Gray
Write-Host "===================================================" -ForegroundColor Cyan

$computeEngineDir = Join-Path $PSScriptRoot "compute_engine"
Set-Location -Path $computeEngineDir
& .\run.ps1
