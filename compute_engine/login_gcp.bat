@echo off
chcp 65001 > nul
echo ===================================================
echo   GCP 계정 로그인 (songpa09@iceu.kr)
echo ===================================================
gcloud.cmd auth login songpa09@iceu.kr --update-adc
gcloud.cmd config set project iceu-songpa09
echo [완료] 계정 및 프로젝트 설정이 완료되었습니다.
pause
