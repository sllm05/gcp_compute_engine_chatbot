@echo off
chcp 65001 > nul
echo ===================================================
echo   Google Cloud Run 로컬 테스트 서버 (포트 8080)
echo ===================================================

set PYTHON_EXE="C:\Users\KIM DONGJUN\miniconda3\envs\myenv\python.exe"

if not exist %PYTHON_EXE% (
    echo [주의] Conda myenv 경로를 찾을 수 없어 시스템 기본 python을 사용합니다.
    set PYTHON_EXE=python
)

set PORT=8080
echo [정보] 서버 실행 중: http://localhost:8080
%PYTHON_EXE% -m uvicorn app:app --host 0.0.0.0 --port 8080 --reload
pause
