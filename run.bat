@echo off
chcp 65001 > nul
echo ===================================================
echo   Google Gemini 3.8 / 3.7 Flash 챗봇 서버 시작
echo   (위치: compute_engine 서브폴더)
echo ===================================================

cd /d "%~dp0compute_engine"
call run.bat
