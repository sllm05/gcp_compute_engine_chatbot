# Google Cloud Run 2: ADC(애플리케이션 기본 사용자 인증 정보) 기반 챗봇

Google Cloud의 **Agent Platform (Vertex AI)** 권장 인증 방식인 **ADC (Application Default Credentials, 애플리케이션 기본 사용자 인증 정보)**를 기반으로 구축된 키리스(Keyless) 서버리스 AI 챗봇 서비스입니다.

---

## 🛡️ ADC(애플리케이션 기본 사용자 인증 정보) 방식의 핵심 장점

Google Cloud 공식 문서 및 Agent Platform에서 권장하는 ADC는 다음과 같은 강력한 보안과 운영상의 이점을 제공합니다:

1. **키리스(Keyless) 무키 아키텍처**:
   - `GEMINI_API_KEY`와 같은 비밀 키를 발급받거나 소스코드, 환경변수, 설정 파일에 저장할 필요가 없습니다.
   - 키 유출, 분실, 주기적 로테이션의 관리 부담이 완전히 제거됩니다.
2. **인프라 자체 ID (Identity-based) 자동 인증**:
   - Google Cloud Run 환경에서는 컨테이너가 기동될 때 Google Cloud 내부 메타데이터 서버(`http://metadata.google.internal`)를 통해 런타임 서비스 계정(`108335720396-compute@developer.gserviceaccount.com`)의 단기 OAuth2 토큰을 자동으로 주입받습니다.
   - Secret Manager 설정(`--set-secrets`) 없이도 안전하게 Agent Platform API를 호출합니다.
3. **IAM 세분화된 접근 제어**:
   - 오직 `roles/aiplatform.user` 역할을 부여받은 서비스 계정만이 모델 추론을 수행할 수 있어 완벽한 엔터프라이즈 보안 거버넌스를 만족합니다.
4. **Agent Platform 최신 모델 지원**:
   - **`Gemini 2.5 Flash`**: 초고속 고효율 지능형 플래시 모델 (기본값)
   - **`Gemini 2.5 Pro`**: 심층 추론, 복잡한 코딩 및 분석에 특화된 고성능 모델

---

## ⚖️ 3대 배포 아키텍처 종합 비교

| 비교 항목 | Compute Engine (`compute_engine/`) | Cloud Run (`cloud_run/`) | Cloud Run 2 (`cloud_run2/`) ⭐ |
| :--- | :--- | :--- | :--- |
| **인증 방식** | Secret Manager ➡️ VM .env 주입 | Secret Manager ➡️ 환경변수 마운트 | **ADC (Keyless 자체 서비스 계정 ID)** |
| **시크릿 키 관리** | 필요 (`GEMINI_API_KEY`) | 필요 (`GEMINI_API_KEY`) | **완전 불필요 (키 유출 위험 0%)** |
| **백엔드 플랫폼** | Google AI Studio | Google AI Studio | **GCP Agent Platform (Vertex AI)** |
| **주요 모델** | Gemini 3.8 / 3.7 Flash | Gemini 3.8 / 3.7 Flash | **Gemini 2.5 Flash / 2.5 Pro** |
| **서버 관리** | IaaS VM (Nginx, systemd 직접 관리) | 서버리스 (Zero-Ops) | **서버리스 (Zero-Ops)** |
| **비용 모델** | 24시간 고정 월 과금 (약 $25) | Scale-to-Zero 초당 종량제 (미사용시 0원) | **Scale-to-Zero 초당 종량제 (미사용시 0원)** |
| **SSL/TLS** | Let's Encrypt Nginx 수동 설정 | Google 관리형 자동 공인 SSL | **Google 관리형 자동 공인 SSL** |

---

## 📁 디렉터리 구성

```text
cloud_run2/
├── app.py                      # ADC 기반 FastAPI 백엔드 (vertexai=True 클라이언트)
├── Dockerfile                  # Python 3.11-slim 기반 OCI 표준 컨테이너 이미지
├── .dockerignore               # 컨테이너 빌드 제외 파일 목록
├── requirements.txt            # 필수 파이썬 라이브러리 목록
├── deploy_to_cloud_run.py      # ADC 기반 Cloud Run 원클릭 배포 스크립트 (Secret 불필요)
├── run.bat                     # 로컬 테스트 실행 배치 스크립트 (포트 8080)
├── run.ps1                     # 로컬 테스트 PowerShell 스크립트
├── README.md                   # 본 문서
└── static/                     # 프론트엔드 웹 UI (Gemini 2.5 Flash/Pro 지원)
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
*로컬 PC에서 테스트할 때는 `gcloud auth application-default login`을 통해 로컬 개발자 ADC를 생성하거나, 배포된 Cloud Run 환경에서 메타데이터 서버를 통해 동작합니다.*

---

## ☁️ Google Cloud Run 배포 방법

### 방법 1. 자동 배포 스크립트 실행 (권장)
```powershell
python deploy_to_cloud_run.py
```
- API 활성화, IAM 권한 부여(`roles/aiplatform.user`), Cloud Build 컨테이너 빌드, Cloud Run 배포 및 실시간 헬스체크/대화 검증까지 일괄 수행됩니다.

### 방법 2. gcloud CLI 직접 배포
```bash
gcloud run deploy gemini-chatbot-adc \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=iceu-songpa09,GOOGLE_CLOUD_LOCATION=us-central1" \
    --min-instances 0 \
    --max-instances 10 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --project iceu-songpa09
```
*Notice: `--set-secrets` 옵션이 전혀 필요하지 않습니다.*
