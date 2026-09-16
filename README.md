# GCP 기반 Gemini 3.8 / 3.7 Flash 챗봇 프로젝트

Google Gemini 공식 웹 UI 스타일을 완벽하게 구현한 **Gemini 3.8 Flash**(기본) 및 **Gemini 3.7 Flash** 듀얼 모델 실시간 대화형 AI 웹 챗봇 프로젝트입니다.  
GCP 인프라 환경에 맞춰 **Compute Engine(IaaS)**과 **Cloud Run(서버리스 컨테이너)** 2가지 배포 아키텍처를 제공합니다.

---

## 📁 디렉터리 구조

```text
gcp_compute_engine_chatbot/
├── .gitignore                          # Git 무시 규칙 (보안 키, 가상환경, 로그 등)
├── README.md                           # 루트 프로젝트 안내 (본 문서)
├── run.bat                             # 루트 편의 실행 배치 파일 (기본 compute_engine 챗봇 실행)
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
└── cloud_run/                          # 🚀 [Serverless] Google Cloud Run 배포 모듈
    ├── README.md                       # Cloud Run 상세 아키텍처 및 설정 가이드
    ├── app.py                          # FastAPI 백엔드 ($PORT 환경변수 동적 리스닝)
    ├── Dockerfile                      # Python 3.11-slim 기반 OCI 표준 컨테이너 이미지 정의
    ├── .dockerignore                   # 컨테이너 빌드 제외 파일 목록
    ├── requirements.txt                # 경량 파이썬 의존성 목록
    ├── deploy_to_cloud_run.py          # Cloud Run 자동 빌드 및 배포 스크립트
    ├── login_gcp.bat                   # GCP 계정 로그인 스크립트
    ├── run.bat / run.ps1               # 로컬 테스트 실행 스크립트 (포트 8080)
    └── static/                         # 챗봇 웹 프론트엔드 (HTML/CSS/JS)
```

---

## ⚖️ 배포 아키텍처 비교

| 비교 항목 | Compute Engine (`compute_engine/`) | Cloud Run (`cloud_run/`) |
| :--- | :--- | :--- |
| **운영 형태** | IaaS 가상머신 (24시간 상시 가동 VM) | 완전 관리형 서버리스 컨테이너 |
| **확장성** | 수동 인스턴스 스케일링 | 0대부터 자동 오토스케일링 (Scale-to-Zero) |
| **비용** | 월 고정 비용 (e2-medium 기준 월 약 $25) | 초당 과금 (요청이 없으면 0원) |
| **SSL/TLS** | Nginx 리버스 프록시 + Let's Encrypt 직접 관리 | Google 관리형 자동 공인 SSL/TLS |
| **배포 방식** | `python compute_engine/deploy_to_compute_engine.py` | `python cloud_run/deploy_to_cloud_run.py` |

---

## 🚀 로컬 실행 방법

### 1. Compute Engine 버전 로컬 테스트 (포트 8000)
```powershell
.\run.ps1
# 또는
cd compute_engine
.\run.ps1
```

### 2. Cloud Run 버전 로컬 테스트 (포트 8080)
```powershell
cd cloud_run
.\run.ps1
```

---

## ☁️ GCP 배포 방법

### 1. Compute Engine 배포
```powershell
python compute_engine/deploy_to_compute_engine.py
```
세부 내용은 [compute_engine/README.md](compute_engine/README.md)를 참고하세요.

### 2. Cloud Run 배포
```powershell
python cloud_run/deploy_to_cloud_run.py
```
세부 내용은 [cloud_run/README.md](cloud_run/README.md)를 참고하세요.
