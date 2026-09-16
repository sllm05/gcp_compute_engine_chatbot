@echo off
chcp 65001 > nul
echo ===================================================
echo   Google Cloud Run 2 (ADC / Agent Platform) 로컬 서버
echo ===================================================

set PYTHON_EXE="C:\Users\KIM DONGJUN\miniconda3\envs\myenv\python.exe"

if not exist %PYTHON_EXE% (
    echo [주의] Conda myenv 경로를 찾을 수 없어 시스템 기본 python을 사용합니다.
    set PYTHON_EXE=python
)

set PORT=8080
set GOOGLE_CLOUD_PROJECT=iceu-songpa09
set GOOGLE_CLOUD_LOCATION=us-central1

echo [정보] 서버 실행 중: http://localhost:8080
echo [정보] 인증 방식: ADC (Application Default Credentials - Keyless)
%PYTHON_EXE% -m uvicorn app:app --host 0.0.0.0 --port 8080 --reload
pause
