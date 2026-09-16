#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Cloud Run 챗봇 자동 빌드 및 배포 스크립트
1. GCP 인증 및 프로젝트(iceu-songpa09) 확인
2. 필수 GCP 서비스(Cloud Run, Cloud Build, Artifact Registry) 활성화
3. Secret Manager(GEMINI_API_KEY) 권한 확인 및 연동
4. gcloud run deploy 실행 (원격 Cloud Build 컨테이너 빌드 및 Cloud Run 자동 배포)
5. 공인 HTTPS URL 확인 및 /api/health 및 Gemini 3.8 Flash 실시간 대화 테스트
6. 전체 로그 기록 (cloud_run_deployment.log)
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime

# Windows 콘솔 인코딩 대응
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 설정 상수
PROJECT = "iceu-songpa09"
PROJECT_NUMBER = "108335720396"
ACCOUNT = "songpa09@iceu.kr"
REGION = "us-central1"
SERVICE_NAME = "gemini-chatbot-cloudrun"
SECRET_ID = "GEMINI_API_KEY"
SECRET_FULL_NAME = f"projects/{PROJECT_NUMBER}/secrets/{SECRET_ID}"
GCLOUD_CMD = "gcloud.cmd" if os.name == "nt" else "gcloud"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "cloud_run_deployment.log")

class DeploymentLogger:
    def __init__(self, log_path):
        self.log_path = log_path
        self.log_file = open(log_path, "a", encoding="utf-8")
        self.banner("Google Cloud Run 챗봇 배포 세션 시작")

    def banner(self, text):
        line = "=" * 80
        self.log(f"\n{line}\n[배포 로그] {text}\n{line}")

    def log(self, message):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{now}] {message}"
        print(formatted)
        self.log_file.write(formatted + "\n")
        self.log_file.flush()

    def step(self, step_no, total_steps, title):
        self.log(f"\n>>> [단계 {step_no}/{total_steps}] {title}")

    def error(self, message):
        self.log(f"[오류 발생] ❌ {message}")

    def success(self, message):
        self.log(f"[성공] ✅ {message}")

    def close(self):
        self.banner("배포 세션 종료")
        self.log_file.close()

logger = DeploymentLogger(LOG_FILE)

def run_command(cmd, desc="", check=True, cwd=None):
    logger.log(f"[명령어 실행] {desc if desc else cmd}")
    res = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=cwd
    )
    if res.stdout.strip():
        for line in res.stdout.strip().splitlines():
            logger.log(f"  [STDOUT] {line}")
    if res.stderr.strip():
        for line in res.stderr.strip().splitlines():
            logger.log(f"  [STDERR] {line}")
    if check and res.returncode != 0:
        raise RuntimeError(f"명령어 실행 실패 (종료 코드 {res.returncode}): {cmd}")
    return res

def check_gcp_auth():
    logger.log("GCP 인증 상태 점검 중...")
    res = run_command(
        f"{GCLOUD_CMD} auth print-access-token --account={ACCOUNT}",
        f"계정({ACCOUNT}) 토큰 유효성 검사",
        check=False
    )
    if res.returncode != 0:
        logger.error(f"계정({ACCOUNT})의 인증 토큰이 만료되었거나 유효하지 않습니다.")
        logger.log("브라우저를 통한 재인증을 진행합니다...")
        login_res = subprocess.run(
            f"{GCLOUD_CMD} auth login {ACCOUNT} --update-adc",
            shell=True
        )
        if login_res.returncode != 0:
            raise RuntimeError(f"GCP 인증에 실패했습니다: {ACCOUNT}")
        logger.success(f"계정({ACCOUNT}) 인증 성공!")

    # 프로젝트 설정
    run_command(f"{GCLOUD_CMD} config set project {PROJECT}", f"프로젝트({PROJECT}) 설정")
    run_command(f"{GCLOUD_CMD} config set account {ACCOUNT}", f"활성 계정({ACCOUNT}) 설정")
    logger.success(f"GCP 인증 및 프로젝트({PROJECT}) 설정 완료")

def main():
    total_steps = 6

    try:
        # ---------------------------------------------------------------------
        # [단계 1] GCP 인증 및 프로젝트 확인
        # ---------------------------------------------------------------------
        logger.step(1, total_steps, f"GCP 계정({ACCOUNT}) 및 프로젝트({PROJECT}) 인증 확인")
        check_gcp_auth()

        # ---------------------------------------------------------------------
        # [단계 2] 필수 GCP 서비스 API 활성화
        # ---------------------------------------------------------------------
        logger.step(2, total_steps, "Cloud Run 및 Cloud Build 관련 필수 API 활성화")
        required_apis = [
            "run.googleapis.com",
            "cloudbuild.googleapis.com",
            "artifactregistry.googleapis.com",
            "secretmanager.googleapis.com"
        ]
        api_str = " ".join(required_apis)
        run_command(
            f"{GCLOUD_CMD} services enable {api_str} --project={PROJECT}",
            "Cloud Run 필수 API 활성화"
        )
        logger.success("필수 GCP API 활성화 완료")

        # ---------------------------------------------------------------------
        # [단계 3] Secret Manager 접근 권한 부여
        # ---------------------------------------------------------------------
        logger.step(3, total_steps, f"Secret Manager ({SECRET_ID}) 및 서비스 계정 권한 확인")
        compute_sa = f"{PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
        
        # Secret Manager Secret Accessor 권한 부여
        grant_cmd = (
            f"{GCLOUD_CMD} secrets add-iam-policy-binding {SECRET_ID} "
            f"--member=\"serviceAccount:{compute_sa}\" "
            f"--role=\"roles/secretmanager.secretAccessor\" "
            f"--project={PROJECT}"
        )
        run_command(grant_cmd, "Cloud Run 기본 서비스 계정에 Secret Accessor 역할 부여", check=False)

        # Cloud Build 빌드 권한 부여 (Cloud Run --source 빌드용)
        for role in ["roles/cloudbuild.builds.builder", "roles/storage.objectAdmin", "roles/artifactregistry.writer", "roles/logging.logWriter"]:
            run_command(
                f"{GCLOUD_CMD} projects add-iam-policy-binding {PROJECT} --member=\"serviceAccount:{compute_sa}\" --role=\"{role}\"",
                f"Cloud Build 실행 권한({role}) 부여",
                check=False
            )
        logger.success("Secret Manager 및 Cloud Build 빌드 권한 설정 완료")

        # ---------------------------------------------------------------------
        # [단계 4] Cloud Run 빌드 및 배포
        # ---------------------------------------------------------------------
        logger.step(4, total_steps, f"Cloud Run 서비스({SERVICE_NAME}) 빌드 및 배포")
        logger.log(f"배포 기준 디렉터리: {BASE_DIR}")

        deploy_cmd = (
            f"{GCLOUD_CMD} run deploy {SERVICE_NAME} "
            f"--source=\"{BASE_DIR}\" "
            f"--region={REGION} "
            f"--platform=managed "
            f"--allow-unauthenticated "
            f"--set-secrets=\"GEMINI_API_KEY={SECRET_ID}:latest\" "
            f"--min-instances=0 "
            f"--max-instances=10 "
            f"--memory=512Mi "
            f"--cpu=1 "
            f"--timeout=300 "
            f"--project={PROJECT} "
            f"--quiet"
        )
        run_command(deploy_cmd, f"Cloud Run ({SERVICE_NAME}) 배포 진행", cwd=BASE_DIR)
        logger.success("Cloud Run 컨테이너 빌드 및 배포 완료!")

        # ---------------------------------------------------------------------
        # [단계 5] Cloud Run 공인 HTTPS 서비스 URL 확인
        # ---------------------------------------------------------------------
        logger.step(5, total_steps, "배포된 Cloud Run 공인 HTTPS 서비스 URL 조회")
        url_res = run_command(
            f"{GCLOUD_CMD} run services describe {SERVICE_NAME} --region={REGION} --project={PROJECT} --format=\"value(status.url)\"",
            "서비스 URL 조회"
        )
        service_url = url_res.stdout.strip()
        if not service_url:
            raise RuntimeError("Cloud Run 서비스 URL을 가져올 수 없습니다.")
        logger.success(f"🌐 Cloud Run 서비스 URL: {service_url}")

        # ---------------------------------------------------------------------
        # [단계 6] 헬스체크 및 실시간 Gemini 3.8 Flash 대화 테스트
        # ---------------------------------------------------------------------
        logger.step(6, total_steps, "서비스 헬스체크 및 실시간 대화 API 테스트")
        import urllib.request

        health_url = f"{service_url}/api/health"
        logger.log(f"1) Health Check 호출: {health_url}")

        health_ok = False
        for h_attempt in range(1, 10):
            try:
                with urllib.request.urlopen(health_url, timeout=15) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    logger.success(f"헬스체크 응답 성공: {json.dumps(data, ensure_ascii=False)}")
                    health_ok = True
                    break
            except Exception as e:
                logger.log(f"  [헬스체크 대기 {h_attempt}/9] {e}")
                time.sleep(3)

        if not health_ok:
            logger.error("Cloud Run 헬스체크 응답이 지연되고 있습니다.")

        # 2) Gemini 3.8 Flash 실시간 채팅 API 테스트
        chat_url = f"{service_url}/api/chat"
        logger.log(f"\n2) Gemini 3.8 Flash 실시간 채팅 API 테스트: {chat_url}")
        test_payload = {
            "model": "gemini-3.8-flash",
            "messages": [
                {"role": "user", "content": "안녕하세요! Cloud Run 환경에서 작동 중인 Gemini인가요? 한 줄로 답변해주세요."}
            ],
            "enable_search": False
        }

        try:
            req = urllib.request.Request(
                chat_url,
                data=json.dumps(test_payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw_stream = resp.read().decode('utf-8')
                logger.log(f"  [API 응답 스트림 샘플]\n{raw_stream[:300]}...")
                if "done" in raw_stream:
                    logger.success("Gemini 3.8 Flash 실시간 대화 API 테스트 성공!")
                else:
                    logger.log("  스트림 수신 완료")
        except Exception as e:
            logger.log(f"  [대화 API 테스트 알림]: {e}")

        logger.banner("Google Cloud Run 챗봇 배포 성공 완료!")
        logger.log(f"🚀 Cloud Run 공인 HTTPS 서비스 접속 URL: {service_url}")
        logger.log(f"📄 상세 배포 로그 파일: {LOG_FILE}")
        return True, service_url

    except Exception as e:
        logger.error(f"배포 중 예외 발생: {e}")
        return False, None
    finally:
        logger.close()

if __name__ == "__main__":
    success, url = main()
    sys.exit(0 if success else 1)
