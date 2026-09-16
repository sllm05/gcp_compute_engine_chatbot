# Google Cloud Run 기반 Gemini 3.8 / 3.7 Flash 챗봇

Google Cloud의 완전 관리형 서버리스 컨테이너 플랫폼인 **Google Cloud Run**에 배포된 **Gemini 3.8 Flash**(기본) 및 **Gemini 3.7 Flash** 실시간 대화형 AI 웹 챗봇입니다.

---

## 🌟 Cloud Run 아키텍처의 장점

1. **완전 관리형 서버리스(Serverless)**:
   - 가상머신(VM)이나 OS 패치, Nginx 서버를 직접 관리할 필요가 없습니다.
   - 요청이 없을 때는 인스턴스가 0대로 축소(Scale to Zero)되어 비용이 전혀 발생하지 않습니다.
2. **Google 관리형 자동 공인 SSL/TLS**:
   - Let's Encrypt를 직접 갱신하거나 도메인 인증 챌린지를 수행할 필요 없이, Google이 제공하는 `*.a.run.app` 도메인과 신뢰할 수 있는 공인 HTTPS가 자동 제공됩니다.
3. **GCP Secret Manager 네이티브 연동**:
   - 소스코드나 로컬 환경에 API 키를 노출하지 않고, Cloud Run 배포 시 Secret Manager의 `GEMINI_API_KEY`를 환경변수로 안전하게 주입합니다.
4. **네이티브 SSE 실시간 스트리밍 지원**:
   - HTTP/2 및 실시간 Server-Sent Events 스트리밍을 네이티브로 지원하여 Gemini AI의 응답이 실시간 글자 단위로 매끄럽게 출력됩니다.

---

## 📁 디렉터리 구성

```text
cloud_run/
├── app.py                      # FastAPI 백엔드 ($PORT 환경변수 동적 리스닝, SSE 스트리밍)
├── Dockerfile                  # Python 3.11-slim 기반 경량 OCI 표준 컨테이너 이미지 빌드 정의
├── .dockerignore               # 컨테이너 빌드 시 제외할 캐시 및 로그 파일 설정
├── requirements.txt            # 필수 파이썬 라이브러리 목록
├── deploy_to_cloud_run.py      # Cloud Run 원클릭 빌드 및 배포 자동화 스크립트
├── login_gcp.bat               # GCP 계정 로그인 배치 파일
├── run.bat                     # 로컬 테스트 실행 배치 파일 (포트 8080)
├── run.ps1                     # 로컬 테스트 실행 PowerShell 스크립트
├── cloud_run_deployment.log    # Cloud Run 배포 진행 로그
└── static/                     # 챗봇 웹 프론트엔드 (Gemini 공식 UI 재현)
    ├── index.html
    ├── style.css
    └── app.js
```

---

## 🚀 로컬 테스트 실행

```powershell
# PowerShell
.\run.ps1
```
```cmd
:: CMD
run.bat
```
브라우저에서 `http://localhost:8080`으로 접속하여 로컬 테스트를 진행할 수 있습니다.

---

## ☁️ Google Cloud Run 배포 방법

### 방법 1. 자동 배포 스크립트 실행 (권장)
배포 자동화 스크립트는 필요한 GCP API 활성화, Secret Manager 접근 권한 부여, 원격 Cloud Build를 통한 컨테이너 이미지 생성 및 Cloud Run 배포, 헬스체크 및 실시간 대화 테스트까지 자동으로 수행합니다.

```powershell
python deploy_to_cloud_run.py
```

### 방법 2. gcloud CLI 직접 배포
```bash
gcloud run deploy gemini-chatbot-cloudrun \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --set-secrets "GEMINI_API_KEY=GEMINI_API_KEY:latest" \
    --min-instances 0 \
    --max-instances 10 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --project iceu-songpa09
```
배포 완료 후 터미널에 출력되는 공인 HTTPS 서비스 URL로 접속하여 서비스를 이용합니다.
