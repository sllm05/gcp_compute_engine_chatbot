# GCP 기반 Gemini 대화형 AI 챗봇 멀티 아키텍처 프로젝트

Google Gemini 공식 웹 UI 스타일을 완벽하게 구현한 실시간 대화형 AI 웹 챗봇 프로젝트입니다.  
GCP 인프라 및 보안 요구사항에 맞춰 **3가지 배포 아키텍처**를 제공합니다:

1. **`compute_engine/`**: IaaS 가상머신(Compute Engine VM) 기반 배포 (Nginx + Let's Encrypt 공인 HTTPS)
2. **`cloud_run/`**: Secret Manager API 키 마운트 기반 서버리스 컨테이너 배포 (Google AI Studio)
3. **`cloud_run2/`**: ⭐ **ADC(Application Default Credentials)** 키리스 기반 서버리스 배포 (GCP Agent Platform / Vertex AI)

---

## 📁 디렉터리 구조

```text
gcp_compute_engine_chatbot/
├── .gitignore                          # Git 무시 규칙 (보안 키, 가상환경, 로그 등)
├── README.md                           # 루트 프로젝트 안내 (본 문서)
├── run.bat                             # 루트 편의 실행 배치 파일
├── run.ps1                             # 루트 편의 실행 PowerShell 스크립트
│
├── compute_engine/                     # 🏢 [IaaS] Google Compute Engine 배포 모듈
│   ├── README.md                       # Compute Engine 상세 아키텍처 및 설정 가이드
│   ├── app.py                          # FastAPI 백엔드 (포트 8000 리스닝)
│   ├── requirements.txt                # 파이썬 의존성 패키지 목록
│   ├── config.yaml                     # Google Cloud Ops Agent VM 모니터링 정책 설정
│   ├── deploy_to_compute_engine.py     # Compute Engine 인스턴스 생성 및 자동 배포 스크립트
│   ├── compute_engine_example.ipynb    # GCP 전 세계 리전 실시간 최저가 분석 및 VM 프로비저닝 노트북
│   ├── login_gcp.bat                   # GCP 계정 로그인 및 프로젝트 설정 스크립트
│   ├── run.bat / run.ps1               # 로컬 실행 스크립트 (포트 8000)
│   ├── static/                         # 챗봇 웹 프론트엔드 (HTML/CSS/JS)
│   └── scripts/                        # VM Nginx 리버스 프록시 및 SSL 설정 스크립트
│
├── cloud_run/                          # 🚀 [Serverless: Secret Manager] Cloud Run 배포 모듈
│   ├── README.md                       # Cloud Run 상세 아키텍처 및 설정 가이드
│   ├── app.py                          # FastAPI 백엔드 ($PORT 환경변수 동적 리스닝)
│   ├── Dockerfile                      # Python 3.11-slim 기반 컨테이너 이미지 정의
│   ├── .dockerignore                   # 컨테이너 빌드 제외 파일 목록
│   ├── requirements.txt                # 경량 파이썬 의존성 목록
│   ├── deploy_to_cloud_run.py          # Cloud Run 자동 빌드 및 배포 스크립트
│   ├── run.bat / run.ps1               # 로컬 테스트 실행 스크립트 (포트 8080)
│   └── static/                         # 챗봇 웹 프론트엔드 (HTML/CSS/JS)
│
└── cloud_run2/                         # 🛡️ [Serverless: ADC Keyless] Agent Platform 배포 모듈
    ├── README.md                       # ADC 아키텍처 상세 가이드
    ├── app.py                          # ADC 기반 FastAPI 백엔드 (vertexai=True 클라이언트)
    ├── Dockerfile                      # Python 3.11-slim 기반 OCI 표준 컨테이너 이미지
    ├── .dockerignore                   # 빌드 제외 파일 목록
    ├── requirements.txt                # 필수 파이썬 의존성 목록
    ├── deploy_to_cloud_run.py          # ADC 기반 Cloud Run 원클릭 배포 스크립트
    ├── run.bat / run.ps1               # 로컬 테스트 실행 스크립트 (포트 8080)
    └── static/                         # 챗봇 웹 프론트엔드 (Gemini 2.5 Flash/Pro 지원)
```

---

## ⚖️ 3대 배포 아키텍처 종합 비교

| 비교 항목 | Compute Engine (`compute_engine/`) | Cloud Run (`cloud_run/`) | Cloud Run 2 (`cloud_run2/`) ⭐ |
| :--- | :--- | :--- | :--- |
| **인증 방식** | Secret Manager ➡️ VM .env 주입 | Secret Manager ➡️ 환경변수 주입 | **ADC (Keyless 자체 서비스 계정 ID)** |
| **시크릿 키 관리** | 필요 (`GEMINI_API_KEY`) | 필요 (`GEMINI_API_KEY`) | **완전 불필요 (키 유출 위험 원천 차단)** |
| **백엔드 플랫폼** | Google AI Studio | Google AI Studio | **GCP Agent Platform (Vertex AI)** |
| **지원 모델** | Gemini 3.8 / 3.7 Flash | Gemini 3.8 / 3.7 Flash | **Gemini 2.5 Flash / 2.5 Pro** |
| **운영 인프라** | 24시간 IaaS 가상머신 (e2-medium) | 완전 관리형 서버리스 컨테이너 | 완전 관리형 서버리스 컨테이너 |
| **비용 모델** | 월 고정 과금 (월 약 $25) | Scale-to-Zero 초당 종량제 (미사용시 0원) | Scale-to-Zero 초당 종량제 (미사용시 0원) |
| **SSL/TLS** | Let's Encrypt Nginx 수동 구성 | Google 관리형 자동 공인 SSL | Google 관리형 자동 공인 SSL |
| **배포 스크립트** | `python compute_engine/deploy_to_compute_engine.py` | `python cloud_run/deploy_to_cloud_run.py` | `python cloud_run2/deploy_to_cloud_run.py` |

---

## 🚀 로컬 실행 방법

### 1. Compute Engine 버전 로컬 테스트 (포트 8000)
```powershell
cd compute_engine
.\run.ps1
```

### 2. Cloud Run 버전 로컬 테스트 (포트 8080)
```powershell
cd cloud_run
.\run.ps1
```

### 3. Cloud Run 2 (ADC 방식) 로컬 테스트 (포트 8080)
```powershell
cd cloud_run2
.\run.ps1
```

---

## ☁️ GCP 배포 방법

- **Compute Engine 배포**: `python compute_engine/deploy_to_compute_engine.py`
- **Cloud Run (Secret Manager) 배포**: `python cloud_run/deploy_to_cloud_run.py`
- **Cloud Run 2 (ADC Keyless) 배포**: `python cloud_run2/deploy_to_cloud_run.py`
