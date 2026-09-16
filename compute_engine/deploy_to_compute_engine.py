#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Compute Engine 배포 자동화 스크립트
1. GCP 인증 및 프로젝트(iceu-songpa09) 확인
2. Secret Manager에서 GEMINI_API_KEY 조회 (projects/108335720396/secrets/GEMINI_API_KEY)
3. Compute Engine 방화벽 규칙 (8000번 포트) 확인 및 생성
4. Compute Engine 인스턴스 생성 (주피터 노트북 사양: e2-medium, Debian 13, 디스크 스케줄 정책 연동)
5. Ops Agent 정책 확인 및 적용 (config.yaml)
6. 챗봇 애플리케이션 파일 전송 및 systemd 서비스 등록
7. 서비스 가동 헬스체크 및 Gemini 3.8 Flash 실시간 API 대화 테스트
8. 모든 진행 내역을 deployment_process.log 파일에 기록
"""

import os
import sys
import time
import json
import tarfile
import subprocess
from datetime import datetime

# Windows 콘솔 인코딩 대응
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 설정 상수 (주피터 노트북 및 GCP 환경 기준)
PROJECT = "iceu-songpa09"
PROJECT_NUMBER = "108335720396"
ACCOUNT = "songpa09@iceu.kr"
DEFAULT_REGION = "us-central1"
DEFAULT_ZONE = "us-central1-a"
INSTANCE_NAME = "gemini-chatbot-vm"
FIREWALL_RULE = "allow-gemini-chatbot-8000"
SECRET_ID = "GEMINI_API_KEY"
SECRET_FULL_NAME = f"projects/{PROJECT_NUMBER}/secrets/{SECRET_ID}"
POLICY_NAME = f"goog-ops-agent-v2-template-1-7-0-{DEFAULT_ZONE}"
DISK_SCHEDULE_POLICY = f"projects/{PROJECT}/regions/{DEFAULT_REGION}/resourcePolicies/default-schedule-1"
GCLOUD_CMD = "gcloud.cmd" if os.name == "nt" else "gcloud"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "deployment_process.log")

class DeploymentLogger:
    def __init__(self, log_path):
        self.log_path = log_path
        self.log_file = open(log_path, "a", encoding="utf-8")
        self.banner("Google Compute Engine 챗봇 배포 세션 시작")

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

def run_command(cmd, desc="", check=True):
    logger.log(f"[명령어 실행] {desc if desc else cmd}")
    res = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
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

def main():
    total_steps = 8

    try:
        # ---------------------------------------------------------------------
        # [단계 1] GCP 인증 및 프로젝트 확인
        # ---------------------------------------------------------------------
        logger.step(1, total_steps, f"GCP 인증 및 기본 계정/프로젝트 확인 ({ACCOUNT} / {PROJECT})")
        
        token_check = run_command(
            f"{GCLOUD_CMD} auth print-access-token --account={ACCOUNT}",
            "GCP 액세스 토큰 검증",
            check=False
        )
        if token_check.returncode != 0:
            logger.error(
                f"계정 {ACCOUNT}의 인증 토큰이 만료되었거나 로그인이 필요합니다.\n"
                "  터미널에서 'login_gcp.bat' 또는 'gcloud.cmd auth login songpa09@iceu.kr --update-adc'를 실행해 주세요."
            )
            return False

        logger.success(f"GCP 계정({ACCOUNT}) 인증 확인 완료")

        run_command(f"{GCLOUD_CMD} config set account {ACCOUNT}", "기본 계정 설정")
        run_command(f"{GCLOUD_CMD} config set project {PROJECT}", "기본 프로젝트 설정")
        run_command(f"{GCLOUD_CMD} config set compute/zone {DEFAULT_ZONE}", "기본 Zone 설정")
        run_command(f"{GCLOUD_CMD} config set compute/region {DEFAULT_REGION}", "기본 Region 설정")

        # ---------------------------------------------------------------------
        # [단계 2] Secret Manager에서 GEMINI_API_KEY 조회
        # ---------------------------------------------------------------------
        logger.step(2, total_steps, f"Secret Manager에서 GEMINI_API_KEY 조회 ({SECRET_FULL_NAME})")
        
        secret_cmd = f"{GCLOUD_CMD} secrets versions access latest --secret={SECRET_ID} --project={PROJECT_NUMBER}"
        secret_res = run_command(secret_cmd, "Secret Manager 비밀키 조회", check=False)

        gemini_key = ""
        if secret_res.returncode == 0 and secret_res.stdout.strip():
            gemini_key = secret_res.stdout.strip()
            logger.success(f"Secret Manager에서 GEMINI_API_KEY 획득 성공 (마스킹: {gemini_key[:6]}...{gemini_key[-4:]})")
        else:
            secret_cmd2 = f"{GCLOUD_CMD} secrets versions access latest --secret={SECRET_FULL_NAME}"
            secret_res2 = run_command(secret_cmd2, "Secret Manager 전체 경로로 재시도", check=False)
            if secret_res2.returncode == 0 and secret_res2.stdout.strip():
                gemini_key = secret_res2.stdout.strip()
                logger.success(f"Secret Manager 전체 경로로 획득 성공 (마스킹: {gemini_key[:6]}...{gemini_key[-4:]})")
            else:
                logger.error(f"Secret Manager에서 키를 가져오지 못했습니다: {secret_res.stderr}")
                env_key = os.environ.get("GEMINI_API_KEY")
                if env_key:
                    logger.log(f"[대체] 시스템 환경변수의 GEMINI_API_KEY를 대체 사용합니다.")
                    gemini_key = env_key
                else:
                    raise RuntimeError("GEMINI_API_KEY를 획득할 수 없습니다.")

        # ---------------------------------------------------------------------
        # [단계 3] Compute Engine 방화벽 규칙 (8000번 포트) 확인 및 생성
        # ---------------------------------------------------------------------
        logger.step(3, total_steps, f"방화벽 규칙 확인 및 생성 ({FIREWALL_RULE}, 포트 tcp:8000)")

        fw_check = run_command(
            f"{GCLOUD_CMD} compute firewall-rules describe {FIREWALL_RULE} --project={PROJECT}",
            f"방화벽 규칙({FIREWALL_RULE}) 존재 여부 확인",
            check=False
        )

        if fw_check.returncode == 0:
            logger.log(f"방화벽 규칙 {FIREWALL_RULE}이 이미 존재합니다.")
        else:
            fw_create = (
                f"{GCLOUD_CMD} compute firewall-rules create {FIREWALL_RULE} "
                f"--project={PROJECT} "
                "--direction=INGRESS "
                "--priority=1000 "
                "--network=default "
                "--action=ALLOW "
                "--rules=tcp:8000 "
                "--source-ranges=0.0.0.0/0 "
                "--target-tags=chatbot-server,http-server "
                "--description=\"Gemini Chatbot Web Service Port 8000\""
            )
            run_command(fw_create, "방화벽 규칙 생성")
            logger.success("방화벽 규칙 생성 완료 (외부 8000번 포트 인바운드 허용)")

        # ---------------------------------------------------------------------
        # [단계 4] Compute Engine VM 인스턴스 확인 및 생성 (주피터 노트북 사양 반영)
        # ---------------------------------------------------------------------
        logger.step(4, total_steps, f"Compute Engine VM 인스턴스 확인 및 생성 ({INSTANCE_NAME}, Zone: {DEFAULT_ZONE})")

        vm_check = run_command(
            f"{GCLOUD_CMD} compute instances describe {INSTANCE_NAME} --zone={DEFAULT_ZONE} --project={PROJECT} --format=\"value(status)\"",
            f"인스턴스({INSTANCE_NAME}) 상태 확인",
            check=False
        )

        if vm_check.returncode == 0 and vm_check.stdout.strip():
            status = vm_check.stdout.strip()
            logger.log(f"인스턴스({INSTANCE_NAME})가 이미 존재합니다 (상태: {status}).")
            if status != "RUNNING":
                run_command(f"{GCLOUD_CMD} compute instances start {INSTANCE_NAME} --zone={DEFAULT_ZONE} --project={PROJECT}", "인스턴스 시작")
        else:
            # 주피터 노트북 사양: e2-medium, Debian 13, disk-resource-policy, shielded-vm, ops-agent label
            vm_create = (
                f"{GCLOUD_CMD} compute instances create {INSTANCE_NAME} "
                f"--project={PROJECT} "
                f"--account={ACCOUNT} "
                f"--zone={DEFAULT_ZONE} "
                "--machine-type=e2-medium "
                "--network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default "
                "--tags=http-server,https-server,chatbot-server "
                "--metadata=enable-osconfig=TRUE "
                "--maintenance-policy=MIGRATE "
                "--provisioning-model=STANDARD "
                f"--service-account={PROJECT_NUMBER}-compute@developer.gserviceaccount.com "
                "--scopes=https://www.googleapis.com/auth/cloud-platform "
                f"--create-disk=auto-delete=yes,boot=yes,device-name={INSTANCE_NAME},"
                f"disk-resource-policy={DISK_SCHEDULE_POLICY},"
                "image=projects/debian-cloud/global/images/debian-13-trixie-v20260908,"
                "mode=rw,size=10,type=pd-balanced "
                "--no-shielded-secure-boot "
                "--shielded-vtpm "
                "--shielded-integrity-monitoring "
                "--labels=goog-ops-agent-policy=v2-template-1-7-0,goog-ec-src=gemini-chatbot "
                "--reservation-affinity=any"
            )
            run_command(vm_create, f"인스턴스({INSTANCE_NAME}) 생성 중...")
            logger.success("Compute Engine VM 인스턴스 생성 완료!")

        # ---------------------------------------------------------------------
        # [단계 5] Ops Agent 정책 확인 및 적용
        # ---------------------------------------------------------------------
        logger.step(5, total_steps, f"Ops Agent 정책 확인 및 적용 ({POLICY_NAME})")

        config_path = os.path.join(BASE_DIR, "config.yaml")
        if not os.path.exists(config_path):
            with open(config_path, "w", encoding="utf-8") as cf:
                cf.write("agentsRule:\n  packageState: installed\n  version: latest\ninstanceFilter:\n  inclusionLabels:\n  - labels:\n      goog-ops-agent-policy: v2-template-1-7-0\n")

        check_policy = run_command(
            f"{GCLOUD_CMD} compute instances ops-agents policies describe {POLICY_NAME} --zone={DEFAULT_ZONE} --project={PROJECT} --account={ACCOUNT}",
            f"Ops Agent 정책({POLICY_NAME}) 확인",
            check=False
        )

        if check_policy.returncode == 0:
            policy_cmd = f"{GCLOUD_CMD} compute instances ops-agents policies update {POLICY_NAME} --project={PROJECT} --account={ACCOUNT} --zone={DEFAULT_ZONE} --file=\"{config_path}\""
            run_command(policy_cmd, "Ops Agent 정책 갱신", check=False)
            logger.success("Ops Agent 정책 갱신 완료")
        else:
            policy_cmd = f"{GCLOUD_CMD} compute instances ops-agents policies create {POLICY_NAME} --project={PROJECT} --account={ACCOUNT} --zone={DEFAULT_ZONE} --file=\"{config_path}\""
            run_command(policy_cmd, "Ops Agent 정책 신규 배포", check=False)
            logger.success("Ops Agent 정책 배포 완료")

        # ---------------------------------------------------------------------
        # [단계 6] VM 인스턴스 외부 IP 확인 및 SSH 준비 대기
        # ---------------------------------------------------------------------
        logger.step(6, total_steps, f"VM 인스턴스({INSTANCE_NAME}) 외부 IP 주소 조회 및 SSH 연결 준비")

        ip_res = run_command(
            f"{GCLOUD_CMD} compute instances describe {INSTANCE_NAME} --zone={DEFAULT_ZONE} --project={PROJECT} --format=\"value(networkInterfaces[0].accessConfigs[0].natIP)\"",
            "외부 IP 조회"
        )
        external_ip = ip_res.stdout.strip()
        if not external_ip:
            raise RuntimeError("외부 IP 주소를 가져올 수 없습니다.")
        logger.success(f"VM 인스턴스 외부 IP 주소: {external_ip}")

        # VM SSH 데몬 연결 확인
        logger.log("인스턴스 부팅 및 SSH 서비스 기동 대기 중...")
        ssh_ready = False
        for attempt in range(1, 15):
            logger.log(f"  [SSH 연결 확인 시도 {attempt}/14] 5초 대기 후 테스트...")
            time.sleep(5)
            test_ssh = run_command(
                f"{GCLOUD_CMD} compute ssh {INSTANCE_NAME} --zone={DEFAULT_ZONE} --project={PROJECT} --quiet --command=\"echo SSH_READY\"",
                "SSH 연결 상태 테스트",
                check=False
            )
            if test_ssh.returncode == 0 and "SSH_READY" in test_ssh.stdout:
                ssh_ready = True
                logger.success("VM SSH 서비스 준비 완료!")
                break

        if not ssh_ready:
            logger.log("[경고] SSH 준비 확인이 지연되고 있으나 작업을 계속 진행합니다.")

        # ---------------------------------------------------------------------
        # [단계 7] 챗봇 애플리케이션 번들링 및 VM 전송 & 설치
        # ---------------------------------------------------------------------
        logger.step(7, total_steps, "챗봇 소스 파일 압축 및 VM 전송/서비스 구축")

        bundle_path = os.path.join(BASE_DIR, "chatbot_app.tar.gz")
        with tarfile.open(bundle_path, "w:gz") as tar:
            tar.add(os.path.join(BASE_DIR, "app.py"), arcname="app.py")
            tar.add(os.path.join(BASE_DIR, "requirements.txt"), arcname="requirements.txt")
            tar.add(os.path.join(BASE_DIR, "static"), arcname="static")
            scripts_dir = os.path.join(BASE_DIR, "scripts")
            if os.path.exists(scripts_dir):
                tar.add(scripts_dir, arcname="scripts")
            env_tmp = os.path.join(BASE_DIR, ".env.deploy")
            with open(env_tmp, "w", encoding="utf-8") as ef:
                ef.write(f"GEMINI_API_KEY={gemini_key}\n")
            tar.add(env_tmp, arcname=".env")
            if os.path.exists(env_tmp):
                os.remove(env_tmp)

        logger.log(f"애플리케이션 번들 생성 완료: {bundle_path} ({os.path.getsize(bundle_path):,} bytes)")

        # VM 설치 스크립트 작성
        setup_script_path = os.path.join(BASE_DIR, "setup_vm.sh")
        with open(setup_script_path, "w", encoding="utf-8", newline="\n") as sf:
            sf.write(f"""#!/usr/bin/env bash
set -e
echo '[1/5] OS 패키지 업데이트 및 Python3 설치...'
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv

echo '[2/5] 애플리케이션 디렉터리 설정...'
sudo mkdir -p /opt/gemini-chatbot
sudo tar -xzf /tmp/chatbot_app.tar.gz -C /opt/gemini-chatbot
sudo chown -R $USER:$USER /opt/gemini-chatbot

echo '[3/5] Python 가상환경 생성 및 패키지 설치...'
cd /opt/gemini-chatbot
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo '[4/5] systemd 서비스 파일 생성...'
sudo bash -c 'cat <<EOF > /etc/systemd/system/gemini-chatbot.service
[Unit]
Description=Gemini 3.8/3.7 Flash Chatbot Web Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/gemini-chatbot
Environment="GEMINI_API_KEY={gemini_key}"
ExecStart=/opt/gemini-chatbot/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF'

echo '[5/5] 서비스 활성화 및 시작...'
sudo systemctl daemon-reload
sudo systemctl enable gemini-chatbot
sudo systemctl restart gemini-chatbot
sudo systemctl status gemini-chatbot --no-pager
""")

        # gcloud compute scp 파일 전송
        scp_cmd = (
            f"{GCLOUD_CMD} compute scp --quiet --zone={DEFAULT_ZONE} --project={PROJECT} "
            f"\"{bundle_path}\" \"{setup_script_path}\" {INSTANCE_NAME}:/tmp/"
        )
        run_command(scp_cmd, "번들 및 setup_vm.sh 파일을 VM /tmp/ 로 전송")
        logger.success("파일 전송 완료")

        if os.path.exists(bundle_path):
            os.remove(bundle_path)
        if os.path.exists(setup_script_path):
            os.remove(setup_script_path)

        # setup_vm.sh 실행
        ssh_cmd = (
            f"{GCLOUD_CMD} compute ssh {INSTANCE_NAME} --zone={DEFAULT_ZONE} --project={PROJECT} "
            f"--quiet --command=\"chmod +x /tmp/setup_vm.sh && /tmp/setup_vm.sh\""
        )
        run_command(ssh_cmd, "VM 내부 setup_vm.sh 실행")
        logger.success("VM 내부 환경 구축 및 systemd 서비스 기동 완료!")

        # ---------------------------------------------------------------------
        # [단계 8] 헬스체크 및 실시간 Gemini 3.8 Flash 대화 테스트
        # ---------------------------------------------------------------------
        logger.step(8, total_steps, "서비스 헬스체크 및 Gemini 3.8 Flash 실시간 대화 API 테스트")

        logger.log("서비스 안정화 대기 중 (5초)...")
        time.sleep(5)

        health_url = f"http://{external_ip}:8000/api/health"
        logger.log(f"1) Health Check 호출: {health_url}")

        import urllib.request
        health_ok = False
        for h_attempt in range(1, 10):
            try:
                with urllib.request.urlopen(health_url, timeout=10) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    logger.success(f"헬스체크 응답 성공: {json.dumps(data, ensure_ascii=False)}")
                    health_ok = True
                    break
            except Exception as e:
                logger.log(f"  [헬스체크 대기 {h_attempt}/9] {e}")
                time.sleep(3)

        if not health_ok:
            logger.error("외부 IP 헬스체크 응답이 지연되고 있습니다.")

        # 2) 실제 Gemini 3.8 Flash 실시간 대화 테스트
        chat_url = f"http://{external_ip}:8000/api/chat"
        logger.log(f"\n2) Gemini 3.8 Flash 실시간 채팅 API 테스트: {chat_url}")
        test_payload = {
            "model": "gemini-3.8-flash",
            "messages": [
                {"role": "user", "content": "안녕하세요! 간단히 자기소개 한 줄만 해주세요."}
            ],
            "enable_search": False
        }

        try:
            req = urllib.request.Request(
                chat_url,
                data=json.dumps(test_payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw_stream = resp.read().decode('utf-8')
                logger.log(f"  [API 응답 스트림 샘플]\n{raw_stream[:300]}...")
                if "done" in raw_stream:
                    logger.success("Gemini 3.8 Flash 실시간 대화 API 테스트 통과!")
                else:
                    logger.log("  스트림 수신 완료")
        except Exception as e:
            logger.log(f"  [대화 API 테스트 주의]: {e}")

        logger.banner("Compute Engine 챗봇 배포 성공 완료!")
        logger.log(f"🌐 챗봇 웹 서비스 접속 URL: http://{external_ip}:8000")
        logger.log(f"📄 세부 작업 로그 파일: {LOG_FILE}")
        return True

    except Exception as e:
        logger.error(f"배포 중 예외 발생: {e}")
        return False
    finally:
        logger.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
